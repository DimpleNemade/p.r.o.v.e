"""Fail-closed case-relative read boundary. No write blocker claim is made."""

import hashlib
import os
import stat
from contextlib import contextmanager
from pathlib import Path, PureWindowsPath

from django.conf import settings


class SourceDenied(ValueError):
    pass


def source_path(case_id, locator):
    if (
        not isinstance(locator, str)
        or not locator
        or "\\" in locator
        or ":" in locator
        or "\x00" in locator
    ):
        raise SourceDenied("Use a relative logical locator with forward slashes")
    parts = locator.split("/")
    if any(
        part in {"", ".", ".."} or part.endswith((".", " ")) or PureWindowsPath(part).is_reserved()
        for part in parts
    ):
        raise SourceDenied("Unsupported locator component")
    root = Path(settings.EVIDENCE_ROOT)
    if not root.is_absolute():
        raise SourceDenied("Storage root must be absolute")
    path = root / str(case_id) / locator
    for component in [*reversed(path.parents), path]:
        info = component.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise SourceDenied("Links and reparse points are disallowed")
    if root.resolve() not in path.resolve().parents:
        raise SourceDenied("Source outside approved root")
    return path


def identity(info):
    return {
        "device": info.st_dev,
        "inode": info.st_ino,
        "size": info.st_size,
        "mtime_ns": info.st_mtime_ns,
        "ctime_ns": info.st_ctime_ns,
    }


def same_identity(left, right):
    # Python 3.12 Windows stat/fstat expose different ctime semantics. Retain
    # ctime in observations, but compare identity/size/mtime across interfaces.
    keys = ("device", "inode", "size", "mtime_ns") if os.name == "nt" else tuple(left)
    return all(left[key] == right[key] for key in keys)


@contextmanager
def opened_source(evidence):
    path = source_path(evidence.case_id, evidence.original_path)
    descriptor = os.open(
        path,
        os.O_RDONLY
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0),
    )
    with os.fdopen(descriptor, "rb") as handle:
        before = os.fstat(handle.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise SourceDenied("Only regular files are supported")
        if before.st_size > settings.MAX_EVIDENCE_BYTES:
            raise SourceDenied("Input exceeds configured size limit")
        source_path(evidence.case_id, evidence.original_path)
        if not same_identity(identity(before), identity(path.stat())):
            raise SourceDenied("Input replaced before read")
        yield handle, identity(before)
        source_path(evidence.case_id, evidence.original_path)
        if not same_identity(
            identity(before), identity(os.fstat(handle.fileno()))
        ) or not same_identity(identity(before), identity(path.stat())):
            raise SourceDenied("Input modified during read")


def read_source(evidence):
    # Bounded immutable bytes are the snapshot used by hashing and extraction.
    with opened_source(evidence) as (handle, metadata):
        content = handle.read(settings.MAX_EVIDENCE_BYTES + 1)
        if len(content) > settings.MAX_EVIDENCE_BYTES or len(content) != metadata["size"]:
            raise SourceDenied("Input size changed or exceeded limit")
    return content, hashlib.sha256(content).hexdigest(), metadata
