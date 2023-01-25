from typing import Dict


def merge_dicts(x: Dict, y: Dict):
    z = x.copy()
    z.update(y)
    return z
