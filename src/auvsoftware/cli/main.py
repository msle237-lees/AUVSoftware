import click

from auvsoftware.database.health import db_ping

@click.group()
def cli():
    """AUVSoftware Command Line Interface."""
    pass


@cli.command()
def status():
    """Check system status."""
    click.echo("AUVSoftware is running.")
    click.echo("Checking database connectivity...")
    if db_ping():
        click.echo("Database connection: OK")
    else:
        click.echo("Database connection: FAILED")
