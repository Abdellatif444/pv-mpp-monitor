from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Union
from datetime import datetime
from dateutil import parser as dtparser

from ..database import get_db
from ..models.sample import Sample, SampleSource
from ..schemas.sample import SampleIn, SampleOut, MPPResponse, SampleImportText
from ..utils.security import verify_write_access
from ..utils.parser import parse_text_samples, parse_csv_bytes, parse_xlsx_bytes
from ..services.mpp import compute_mpp
from ..services.websocket import manager, sample_to_message

router = APIRouter()


def _to_model(item: SampleIn) -> Sample:
    # Do not set timestamp=None so that server_default applies when not provided
    s = Sample(
        voltage=item.V,
        current=item.I,
        power=item.P if item.P is not None else item.V * item.I,
        temperature=item.T,
        source=item.source or SampleSource.MANUAL,
    )
    if item.t:
        s.timestamp = item.t
    return s


def _to_out(model: Sample) -> SampleOut:
    return SampleOut(
        id=model.id,
        t=model.timestamp,
        V=model.voltage,
        I=model.current,
        P=model.power if model.power is not None else (model.voltage * model.current),
        T=model.temperature,
        source=model.source,
    )


@router.post("/api/samples", response_model=List[SampleOut], dependencies=[Depends(verify_write_access)])
async def create_samples(
    payload: Union[SampleIn, List[SampleIn]],
    db: Session = Depends(get_db),
):
    items = payload if isinstance(payload, list) else [payload]
    created: List[Sample] = []

    for it in items:
        # Deduplicate by (t,V,I) if t provided
        existing = None
        if it.t is not None:
            existing = (
                db.query(Sample)
                .filter(Sample.timestamp == it.t, Sample.voltage == it.V, Sample.current == it.I)
                .first()
            )
        if existing:
            # Update if power missing
            if existing.power is None:
                existing.power = it.P if it.P is not None else it.V * it.I
            if it.T is not None:
                existing.temperature = it.T
            db.add(existing)
            db.flush()
            created.append(existing)
        else:
            obj = _to_model(it)
            db.add(obj)
            db.flush()
            created.append(obj)

    db.commit()

    # Broadcast over WebSocket
    for s in created:
        await manager.broadcast(sample_to_message(s.to_dict()))

    return [_to_out(s) for s in created]


@router.post("/api/import/file", response_model=List[SampleOut], dependencies=[Depends(verify_write_access)])
async def import_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Import CSV or XLSX from an uploaded file."""
    content = await file.read()
    filename = (file.filename or "").lower()
    ctype = (file.content_type or "").lower()

    try:
        if filename.endswith(".xlsx") or "spreadsheetml" in ctype:
            parsed = parse_xlsx_bytes(content)
        else:
            parsed = parse_csv_bytes(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    if not parsed:
        raise HTTPException(status_code=400, detail="No valid rows found in file")

    items: List[SampleIn] = []
    for d in parsed:
        items.append(SampleIn(**d, source=SampleSource.IMPORT))

    created: List[Sample] = []
    for it in items:
        obj = _to_model(it)
        db.add(obj)
        db.flush()
        created.append(obj)

    db.commit()

    for s in created:
        await manager.broadcast(sample_to_message(s.to_dict()))

    return [_to_out(s) for s in created]


@router.delete("/api/samples", dependencies=[Depends(verify_write_access)])
async def delete_all_samples(db: Session = Depends(get_db)):
    """Delete all samples (reset)."""
    try:
        count = db.query(Sample).delete()
        db.commit()
        return {"deleted": count}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/samples", response_model=List[SampleOut])
async def list_samples(
    from_: Optional[str] = Query(None, alias="from"),
    to_: Optional[str] = Query(None, alias="to"),
    limit: Optional[int] = Query(None, ge=1, le=10000),
    db: Session = Depends(get_db),
):
    q = db.query(Sample)

    if from_:
        try:
            dt_from = dtparser.isoparse(from_)
            q = q.filter(Sample.timestamp >= dt_from)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid 'from' datetime format")

    if to_:
        try:
            dt_to = dtparser.isoparse(to_)
            q = q.filter(Sample.timestamp <= dt_to)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid 'to' datetime format")

    q = q.order_by(Sample.timestamp.asc())
    if limit:
        q = q.limit(limit)

    rows = q.all()
    return [_to_out(r) for r in rows]


@router.get("/api/mpp", response_model=MPPResponse)
async def get_mpp(
    from_: Optional[str] = Query(None, alias="from"),
    to_: Optional[str] = Query(None, alias="to"),
    db: Session = Depends(get_db),
):
    q = db.query(Sample)

    if from_:
        try:
            dt_from = dtparser.isoparse(from_)
            q = q.filter(Sample.timestamp >= dt_from)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid 'from' datetime format")

    if to_:
        try:
            dt_to = dtparser.isoparse(to_)
            q = q.filter(Sample.timestamp <= dt_to)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid 'to' datetime format")

    q = q.order_by(Sample.timestamp.asc())
    rows = q.all()

    series = [r.to_dict() for r in rows]
    mpp = compute_mpp(series)
    if not mpp:
        raise HTTPException(status_code=404, detail="No data to compute MPP")

    idx, s = mpp
    return MPPResponse(Vmp=s['V'], Imp=s['I'], Pmp=s['P'], index=idx, t=dtparser.isoparse(s['t']) if isinstance(s['t'], str) else s['t'])


@router.post("/api/import/text", response_model=List[SampleOut], dependencies=[Depends(verify_write_access)])
async def import_text(
    request: Request,
    db: Session = Depends(get_db),
):
    content_type = request.headers.get('content-type', '')
    text_data: str
    source = SampleSource.IMPORT
    if content_type.startswith('text/plain'):
        raw = await request.body()
        text_data = raw.decode('utf-8', errors='ignore')
    else:
        # Expect JSON with {"text": "...", "source"?: "IMPORT"}
        body = await request.json()
        text_data = body.get('text', '') if isinstance(body, dict) else ''
        if 'source' in body and body['source'] in SampleSource.__members__:
            source = SampleSource[body['source']]

    parsed = parse_text_samples(text_data)
    if not parsed:
        raise HTTPException(status_code=400, detail="No valid lines found in input text")

    # Convert parsed dicts to SampleIn models
    items: List[SampleIn] = []
    for d in parsed:
        items.append(SampleIn(**d, source=source))

    # Insert
    created: List[Sample] = []
    for it in items:
        obj = _to_model(it)
        db.add(obj)
        db.flush()
        created.append(obj)

    db.commit()

    for s in created:
        await manager.broadcast(sample_to_message(s.to_dict()))

    return [_to_out(s) for s in created]
