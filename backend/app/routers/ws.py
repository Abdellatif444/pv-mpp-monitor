from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.websocket import manager

router = APIRouter()

@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive by reading messages; ignore their content
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
