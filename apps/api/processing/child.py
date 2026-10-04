"""Versioned metadata adapter; no source event timestamp is inferred."""

import hashlib
import json
import sys
from pathlib import Path

source = Path(sys.argv[1])
data = source.read_bytes()
print(
    json.dumps(
        {"sizeBytes": len(data), "sha256": hashlib.sha256(data).hexdigest()},
        sort_keys=True,
        separators=(",", ":"),
    )
)
