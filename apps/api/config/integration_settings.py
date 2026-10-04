"""PostgreSQL/Redis/team-boundary acceptance profile; environment must be explicit."""

import os

os.environ["PROVE_PROFILE"] = "team"
from .settings import *

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
