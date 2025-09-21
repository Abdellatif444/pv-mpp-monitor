from typing import List, Dict, Any, Optional, Tuple


def compute_mpp(samples: List[Dict[str, Any]]) -> Optional[Tuple[int, Dict[str, Any]]]:
    """Compute the Maximum Power Point from a list of samples.

    Each sample is expected to have keys: 'V', 'I', 'P' (optional), 't'.
    Returns a tuple of (index, sample_dict) for the MPP, or None if empty.
    """
    if not samples:
        return None
    max_index = -1
    max_power = float('-inf')
    max_sample: Optional[Dict[str, Any]] = None

    for idx, s in enumerate(samples):
        V = s.get('V')
        I = s.get('I')
        P = s.get('P', None)
        if P is None and V is not None and I is not None:
            P = V * I
        if P is None:
            continue
        if P > max_power:
            max_power = P
            max_index = idx
            max_sample = {
                **s,
                'P': P,  # ensure P is present
            }
    if max_sample is None:
        return None
    return max_index, max_sample
