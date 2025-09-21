import re
from typing import List, Dict, Any
from datetime import datetime

LINE_REGEX = re.compile(
    r"V\s*:\s*([+-]?[0-9]*\.?[0-9]+)\s*V\b.*?I\s*:\s*([+-]?[0-9]*\.?[0-9]+)\s*A\b(?:.*?P\s*:\s*([+-]?[0-9]*\.?[0-9]+)\s*W\b)?(?:.*?T\s*:\s*([+-]?[0-9]*\.?[0-9]+)\s*°?C\b)?",
    re.IGNORECASE,
)


def parse_text_samples(text: str) -> List[Dict[str, Any]]:
    """Parse multiline text containing lines like 'V:20.2V I:0.10A P:2.1W' into sample dicts.

    Returns list of dicts with keys: V, I, P (optional), T (optional), t (now).
    Ignores lines that don't match.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return []

    samples: List[Dict[str, Any]] = []

    # Try CSV with header first (',' or ';')
    delim = ';' if ';' in lines[0] else ','
    header_parts = [p.strip().lower() for p in lines[0].split(delim)]
    if ('v' in header_parts and 'i' in header_parts) or ('voltage' in header_parts and 'current' in header_parts):
        header = header_parts
        for row in lines[1:]:
            parts = [p.strip() for p in row.split(delim)]
            if len(parts) != len(header):
                continue
            data: Dict[str, Any] = {}
            for key, val in zip(header, parts):
                if key in ('t', 'time', 'timestamp'):
                    data['t'] = val
                elif key in ('v', 'voltage'):
                    data['V'] = float(val)
                elif key in ('i', 'current'):
                    data['I'] = float(val)
                elif key in ('p', 'power'):
                    data['P'] = float(val)
                elif key in ('t_c', 'temp', 'temperature'):
                    data['T'] = float(val)
            if 'V' in data and 'I' in data:
                if 'P' not in data:
                    data['P'] = data['V'] * data['I']
                samples.append(data)
        return samples

    # Try plain CSV without header (V,I[,P][,T]) with ',' or ';'
    csv_like = True
    for ln in lines:
        if not re.match(r"^\s*[+-]?[0-9]*\.?[0-9]+\s*[,;]\s*[+-]?[0-9]*\.?[0-9]+(\s*[,;]\s*[+-]?[0-9]*\.?[0-9]+){0,2}\s*$", ln):
            csv_like = False
            break
    if csv_like:
        for ln in lines:
            d = ';' if ';' in ln else ','
            parts = [p.strip() for p in ln.split(d)]
            if len(parts) < 2:
                continue
            V = float(parts[0])
            I = float(parts[1])
            P = float(parts[2]) if len(parts) >= 3 and parts[2] != '' else V * I
            T = float(parts[3]) if len(parts) >= 4 and parts[3] != '' else None
            samples.append({'V': V, 'I': I, 'P': P, 'T': T})
        return samples

    # Fallback to key-value regex lines
    for line in lines:
        m = LINE_REGEX.search(line)
        if not m:
            continue
        V = float(m.group(1))
        I = float(m.group(2))
        P = float(m.group(3)) if m.group(3) is not None else None
        T = float(m.group(4)) if m.group(4) is not None else None
        samples.append({
            'V': V,
            'I': I,
            'P': P if P is not None else V * I,
            'T': T,
            't': datetime.utcnow().isoformat() + 'Z'
        })
    return samples
