"""Offline standard-library-only verifier. Never extracts archive contents."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/api"))
from reporting.package import verify, MAX_BYTES

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: verify_package.py <package.zip>", file=sys.stderr)
        sys.exit(2)
    try:
        with Path(sys.argv[1]).open("rb") as handle:
            data = handle.read(MAX_BYTES + 1)
        print(json.dumps(verify(data), indent=2))
    except Exception as exc:
        print(json.dumps({"valid": False, "error": str(exc)}))
        sys.exit(1)
