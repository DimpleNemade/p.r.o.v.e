"""Small, dependency-light worker boundary for local and future service use."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path


@dataclass
class ProcessingResult:
    status: str
    calculated_hash: str = ""
    warnings: list[str] | None = None
    error: str = ""


def submit_job(job_reference: str) -> str:
    return job_reference


def get_job_status(job_reference: str) -> str:
    return "queued"


def process_evidence(path: str, expected_hash: str = "") -> ProcessingResult:
    source = Path(path)
    if not source.is_file():
        return ProcessingResult(status="failed", error="Evidence path is not readable", warnings=[])
    digest = sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    calculated = digest.hexdigest()
    if expected_hash and expected_hash.lower() != calculated:
        return ProcessingResult(
            status="failed", calculated_hash=calculated, error="SHA-256 mismatch", warnings=[]
        )
    return ProcessingResult(
        status="succeeded", calculated_hash=calculated, warnings=["Basic metadata only"]
    )


def record_processing_run(*args, **kwargs):
    return {"status": "recorded"}


def record_artifact(*args, **kwargs):
    return {"status": "recorded"}


def record_provenance(*args, **kwargs):
    return {"status": "recorded"}


def record_failure(*args, **kwargs):
    return {"status": "recorded"}
