import hashlib
import json
from typing import Any, Dict, List, Union


def compute_sha256(data: Union[str, bytes, Dict[str, Any], List[Any]]) -> str:
    """Computes a deterministic SHA-256 hexadecimal hash for strings, bytes, or JSON-serializable objects."""
    if isinstance(data, bytes):
        raw_bytes = data
    elif isinstance(data, str):
        raw_bytes = data.encode("utf-8")
    else:
        raw_bytes = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")

    return hashlib.sha256(raw_bytes).hexdigest()
