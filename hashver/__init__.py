__version__ = "0.1.0"

import click
from git import Repo
from datetime import date


@click.group()
def cli():
    pass


@cli.command()
def version():
    d = date.today()
    repo = Repo(".")
    version = f"{d.year}-{d.month:02}-{str(repo.heads.master.commit)[:8]}"
    click.echo(version)
