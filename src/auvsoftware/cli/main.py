from __future__ import annotations

import click
import uvicorn
import time


@click.group()
def cli():
    """AUVSoftware Command Line Interface."""
    pass

# -----------------------------------
# Run only database and API
# -----------------------------------
@cli.command()
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8000, show_default=True, type=int)
@click.option("--reload", is_flag=True, help="Enable auto-reload for development.")
def runAPI(host: str, port: int, reload: bool) -> None:
    """
    Run only the API server.
    """
    click.echo("Starting AUVSoftware API server...")

    # Use subprocess to ensure the compose file is up and the database container is created
    import subprocess
    subprocess.run(["docker", "compose", "up", "-d"], check=True)
    time.sleep(7.5)  # Wait a moment for the database to be ready

    # Ensure the database compose file is up before starting the API
    from auvsoftware.database.scripts.init_db import init_db
    init_db()

    uvicorn.run("auvsoftware.api.app:app", host=host, port=port, reload=reload) 

# -----------------------------------
# Run all services
# -----------------------------------
@cli.command()
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8000, show_default=True, type=int)
@click.option("--reload", is_flag=True, help="Enable auto-reload for development.")
def runAll(host: str, port: int, reload: bool) -> None:
    """
    Run all services including the API server and background tasks.
    """
    click.echo("Starting all AUVSoftware services...")

    # Use subprocesses to ensure the compose file is up and the database container is created
    import subprocess
    subprocess.run(["docker", "compose", "up", "-d"], check=True)
    time.sleep(7.5)  # Wait a moment for the database to be ready

    # Ensure the database compose file is up before starting the API
    from auvsoftware.database.scripts.init_db import init_db
    init_db()

    # Start the API server in a separate thread
    from threading import Thread
    api_thread = Thread(target=uvicorn.run, args=("auvsoftware.api.app:app",), kwargs={"host": host, "port": port, "reload": reload})
    api_thread.start()
    
    time.sleep(5)  # Wait a moment for the API to start
    
    # Ensure a run is created for the controller to use
    from auvsoftware.database.scripts.run_create import run_create
    run_create(run_name="Initial Run", platform="linux", vehicle="string", operator="user", notes="Initial run for controller", config="{}")
    
    # Start the controller in a separate thread
    from auvsoftware.controller import run_controller
    controller_thread = Thread(target=run_controller)
    controller_thread.start()
    
    click.echo("All services started successfully.")
    