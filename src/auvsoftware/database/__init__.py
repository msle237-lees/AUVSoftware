"""
Database package for AUVSoftware.

Provides configuration, engine/session factories, ORM base, and utilities
for checking database health.

This package is intentionally client-focused: Postgres runs in Docker
(Compose) and this code connects to it.
"""