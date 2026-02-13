from __future__ import annotations

import click
import uvicorn


@click.group()
def cli():
    """AUVSoftware Command Line Interface."""
    pass


# -----------------------------------
# Init DB
# -----------------------------------
@cli.command()
@click.option(
    "--drop-first",
    is_flag=True,
    help="Drop existing tables before creating them (useful for development resets).",
)
def initdb(drop_first: bool) -> None:
    """
    Initialize the database schema.
    """
    from auvsoftware.database.scripts.init_db import init_db

    click.echo("Initializing database schema...")
    init_db()
    click.echo("Database initialized successfully.")


# -----------------------------------
# Status Check
# -----------------------------------
@cli.command()
def status() -> None:
    """Check system status."""
    from auvsoftware.database.health import db_ping

    click.echo("AUVSoftware is running.")
    click.echo("Checking database connectivity...")
    if db_ping():
        click.echo("Database connection: OK")
    else:
        click.echo("Database connection: FAILED")


# -----------------------------------
# Database Only execution
# -----------------------------------
@cli.command()
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8000, show_default=True, type=int)
@click.option("--reload", is_flag=True, help="Enable auto-reload for development.")
def dbonly(host: str, port: int, reload: bool) -> None:
    """
    Run the FastAPI server using Uvicorn.
    """
    click.echo(f"Starting API server on {host}:{port} (reload={reload})")

    uvicorn.run(
        "auvsoftware.api.app:app",
        host=host,
        port=port,
        reload=reload,
    )