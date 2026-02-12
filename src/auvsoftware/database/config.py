"""
 * @file config.py
 * @brief Database configuration loader for AUVSoftware.
 *
 * Loads environment variables from a `.env` file (if present) and builds a
 * SQLAlchemy DATABASE_URL for PostgreSQL.
 *
 * Expected environment variables:
 * - POSTGRES_DB
 * - POSTGRES_USER
 * - POSTGRES_PASSWORD
 * - DB_HOST (optional; defaults to "localhost")
 * - DB_PORT (optional; defaults to "5432")
 *
 * If you later run the API inside Docker, set DB_HOST=db (Compose service name).
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load .env from project root if present (safe to call multiple times).
load_dotenv()


@dataclass(frozen=True)
class DatabaseSettings:
    """Database configuration settings."""
    postgres_db: str
    postgres_user: str
    postgres_password: str
    host: str = "localhost"
    port: str = "5432"


def load_db_settings() -> DatabaseSettings:
    """
    /**
     * @brief Load database settings from environment variables.
     * @return DatabaseSettings populated from env vars.
     * @throws RuntimeError if required values are missing.
     */
    """
    db = os.getenv("POSTGRES_DB")
    user = os.getenv("POSTGRES_USER")
    pwd = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")

    missing = [k for k, v in {
        "POSTGRES_DB": db,
        "POSTGRES_USER": user,
        "POSTGRES_PASSWORD": pwd,
    }.items() if not v]

    if missing:
        raise RuntimeError(
            f"Missing required database environment variables: {', '.join(missing)}"
        )

    return DatabaseSettings(
        postgres_db=db,  # type: ignore[arg-type]
        postgres_user=user,  # type: ignore[arg-type]
        postgres_password=pwd,  # type: ignore[arg-type]
        host=host,
        port=port,
    )


def build_database_url(settings: DatabaseSettings) -> str:
    """
    /**
     * @brief Build a PostgreSQL SQLAlchemy URL from settings.
     * @param settings DatabaseSettings.
     * @return SQLAlchemy connection string using psycopg2 driver.
     *
     * Format:
     * postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DB
     */
    """
    # NOTE: If your password can contain special characters, prefer URL-encoding.
    # For most local dev passwords, this is fine.
    return (
        f"postgresql+psycopg2://{settings.postgres_user}:"
        f"{settings.postgres_password}@{settings.host}:{settings.port}/{settings.postgres_db}"
    )


# Loaded on import for convenience. If you prefer lazy loading, remove these.
DB_SETTINGS = load_db_settings()
DATABASE_URL = build_database_url(DB_SETTINGS)