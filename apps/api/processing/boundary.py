"""Restricted Linux child in team mode; synthetic-only development execution."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from django.conf import settings


def run_metadata(content, synthetic):
    if settings.PROFILE != "team" and not synthetic:
        raise ValueError("Local execution is synthetic-development mode only")
    if len(content) > settings.MAX_EVIDENCE_BYTES:
        raise ValueError("Input limit exceeded")
    root = Path(settings.OUTPUT_ROOT) / "scratch"
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="run-", dir=root) as directory:
        scratch = Path(directory)
        source = scratch / "input"
        source.write_bytes(content)
        child = Path(__file__).with_name("child.py")
        command = [sys.executable, "-I", str(child), str(source)]
        options = {}
        if settings.PROFILE == "team":
            if sys.platform != "linux" or not shutil.which("bwrap"):
                raise ValueError("Team requires Linux bubblewrap; no unsandboxed fallback")
            command = [
                "bwrap",
                "--unshare-all",
                "--die-with-parent",
                "--new-session",
                "--cap-drop",
                "ALL",
                "--ro-bind",
                "/usr",
                "/usr",
            ]
            for system_dir in ("/lib", "/lib64", "/bin"):
                if Path(system_dir).exists():
                    command += ["--ro-bind", system_dir, system_dir]
            command += [
                "--proc",
                "/proc",
                "--dev",
                "/dev",
                "--tmpfs",
                "/tmp",
                "--ro-bind",
                str(source),
                "/input",
                "--ro-bind",
                str(child),
                "/processor.py",
                "--clearenv",
                "--setenv",
                "PATH",
                "/usr/bin",
                "--",
                "/usr/bin/python3",
                "-I",
                "/processor.py",
                "/input",
            ]

            def limits():
                import resource

                resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024,) * 2)
                resource.setrlimit(resource.RLIMIT_CPU, (settings.PROCESSING_TIMEOUT,) * 2)
                resource.setrlimit(resource.RLIMIT_FSIZE, (65536,) * 2)
                resource.setrlimit(resource.RLIMIT_NOFILE, (32,) * 2)
                os.umask(0o077)

            options["preexec_fn"] = limits
        with (scratch / "stdout").open("w+b") as stdout, (scratch / "stderr").open("w+b") as stderr:
            result = subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                timeout=settings.PROCESSING_TIMEOUT,
                env={"SYSTEMROOT": os.environ.get("SYSTEMROOT", "")} if os.name == "nt" else {},
                **options,
            )
            if result.returncode:
                raise ValueError("Restricted metadata processor failed")
            stdout.seek(0)
            raw = stdout.read(65537)
            if len(raw) > 65536:
                raise ValueError("Processor output exceeded limit")
        output = json.loads(raw)
        if set(output) != {"sizeBytes", "sha256"} or output["sizeBytes"] != len(content):
            raise ValueError("Invalid processor output schema")
        return output
