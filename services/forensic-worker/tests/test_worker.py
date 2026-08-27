from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from worker import process_evidence


def test_hashes_without_exposing_contents(tmp_path: Path):
    source = tmp_path / "sample.txt"
    source.write_text("synthetic evidence", encoding="utf-8")
    result = process_evidence(str(source))
    assert result.status == "succeeded"
    assert len(result.calculated_hash) == 64


def test_mismatch_fails(tmp_path: Path):
    source = tmp_path / "sample.txt"
    source.write_text("synthetic evidence", encoding="utf-8")
    result = process_evidence(str(source), "0" * 64)
    assert result.status == "failed"
    assert result.error == "SHA-256 mismatch"
