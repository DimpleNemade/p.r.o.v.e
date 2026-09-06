import hashlib
from pathlib import Path


def calculate_sha256(path: str) -> str:
    """Hash a source file without reading its contents into logs or API responses."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_evidence(evidence):
    path = Path(evidence.original_path)
    if not path.is_file():
        return "", "unreadable"
    calculated = calculate_sha256(str(path))
    status = (
        "verified"
        if not evidence.expected_hash or evidence.expected_hash.lower() == calculated
        else "mismatch"
    )
    return calculated, status
