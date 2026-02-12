import click


@click.group()
def cli():
    """AUVSoftware Command Line Interface."""
    pass


@cli.command()
def status():
    """Check system status."""
    from auvsoftware.database.health import db_ping
    click.echo("AUVSoftware is running.")
    click.echo("Checking database connectivity...")
    if db_ping():
        click.echo("Database connection: OK")
    else:
        click.echo("Database connection: FAILED")

@cli.command()
def initdb():
    """Initialize the database schema."""
    from auvsoftware.database.scripts.init_db import init_db
    click.echo("Initializing database schema...")
    init_db()
    click.echo("Database initialized successfully.")
    
