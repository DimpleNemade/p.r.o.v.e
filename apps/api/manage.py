#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    # Root-level invocation otherwise searches the workspace directory and
    # misses the Django app beneath apps/api.
    if len(sys.argv) == 2 and sys.argv[1] == "test":
        sys.argv.append("cases")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
