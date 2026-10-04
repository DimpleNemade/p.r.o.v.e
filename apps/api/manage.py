#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    # Always operate from the Django project directory (this file's location) so
    # that test discovery, fixtures and relative paths behave identically whether
    # manage.py is invoked from here or from the repository root. Without this,
    # `python apps/api/manage.py test` run from the root discovers zero tests
    # because Django searches the current working directory.
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
