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
def initdb() -> None:
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
    
# -----------------------------------
# Run all services
# -----------------------------------
@cli.command()
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8000, show_default=True, type=int)
@click.option("--reload", is_flag=True, help="Enable auto-reload for development.")
def run(host: str, port: int, reload: bool) -> None:
    """
    Run all services including the API server and background tasks.
    """
    click.echo("Starting all AUVSoftware services...")

    # Start the API server in a separate thread
    from threading import Thread

    # Ensure the database compose file is up before starting the API
    from auvsoftware.database.scripts.init_db import init_db
    init_db()

    api_thread = Thread(target=uvicorn.run, args=("auvsoftware.api.app:app",), kwargs={"host": host, "port": port, "reload": reload})
    api_thread.start()
    
    click.echo("All services started successfully.")