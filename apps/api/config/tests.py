import os
import subprocess
import sys
import tempfile
from pathlib import Path

from django.test import SimpleTestCase


class TeamConfigurationTests(SimpleTestCase):
    def _run_settings_import(self, overrides):
        environment = os.environ.copy()
        environment.update(overrides)
        return subprocess.run(
            [sys.executable, "-c", "import config.settings"],
            cwd=Path(__file__).resolve().parent.parent,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_team_profile_rejects_development_secret(self):
        result = self._run_settings_import(
            {"PROVE_PROFILE": "team", "SECRET_KEY": "development-secret"}
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("strong non-development SECRET_KEY", result.stderr)

    def test_non_postgresql_database_url_is_rejected(self):
        result = self._run_settings_import(
            {"PROVE_PROFILE": "team", "DATABASE_URL": "sqlite:///unsafe.sqlite3"}
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be a postgresql:// URL", result.stderr)

    def test_explicit_team_profile_passes_settings_import(self):
        with tempfile.TemporaryDirectory(prefix="prove-team-settings-") as root:
            evidence = Path(root) / "evidence"
            output = Path(root) / "output"
            evidence.mkdir()
            output.mkdir()
            result = self._run_settings_import(
                {
                    "PROVE_PROFILE": "team",
                    "SECRET_KEY": "test-only-strong-secret-0123456789-abcdefghijklmnopqrstuvwxyz-ABCDE",
                    "DATABASE_URL": "postgresql://user:pass@127.0.0.1:5432/forensic",
                    "REDIS_URL": "redis://127.0.0.1:6379/0",
                    "ALLOWED_HOSTS": "127.0.0.1",
                    "CSRF_TRUSTED_ORIGINS": "https://127.0.0.1",
                    "CORS_ALLOWED_ORIGINS": "https://127.0.0.1",
                    "EVIDENCE_ROOT": str(evidence.resolve()),
                    "OUTPUT_ROOT": str(output.resolve()),
                    "CELERY_TASK_ALWAYS_EAGER": "false",
                }
            )
        self.assertEqual(result.returncode, 0, result.stderr)
