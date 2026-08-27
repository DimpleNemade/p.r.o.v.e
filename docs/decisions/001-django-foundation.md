# ADR-001: Django as platform foundation

Status: accepted.

Django provides mature sessions, password hashing, CSRF middleware, ORM, migrations, admin, and a custom user model from day one. The trade-off is a Python-centric backend, accepted because worker and API domain logic share the same ecosystem.
