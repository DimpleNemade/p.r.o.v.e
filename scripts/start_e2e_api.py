"""Playwright-only API process; fresh root or explicit retained test root."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

workspace = Path(__file__).resolve().parents[1]
root = Path(os.environ.get("PROVE_E2E_ROOT") or tempfile.mkdtemp(prefix="prove-e2e-"))
root.mkdir(parents=True, exist_ok=True)
marker = root / ".prove-test-root"
if any(root.iterdir()) and not marker.exists():
    raise SystemExit("Refusing non-test directory")
marker.touch()
env = {
    **os.environ,
    "DJANGO_SETTINGS_MODULE": "config.test_settings",
    "PROVE_TEST_ROOT": str(root),
    "PROVE_PROFILE": "test",
}
api = workspace / "apps/api"
print(f"Isolated browser storage: {root}", flush=True)
for command in (["migrate", "--noinput"], ["seed_demo"]):
    subprocess.run([sys.executable, "manage.py", *command], cwd=api, env=env, check=True)
subprocess.run(
    [sys.executable, "manage.py", "runserver", "127.0.0.1:8017", "--noreload"],
    cwd=api,
    env=env,
    check=True,
)
