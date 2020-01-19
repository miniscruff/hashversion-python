__version__ = "0.1.0"

import click
from git import Repo
from datetime import date
import toml


class Config:
    def __init__(self):
        try:
            with open("pyproject.toml") as toml_file:
                toml_config = toml.load(toml_file)["tool"]["hashver"]
        except Exception as e:
            toml_config = {}

        #: How many characters of the git hash to include.
        #: Defaults to 8, recommended 6-10 but anything is allowed
        self.hash_length = toml_config.get("hash_length", 8)
        #: Whether or not to include a 2 digit day in your version
        self.use_day = toml_config.get("use_day", False)


@click.group()
def cli():
    pass


@cli.command()
def configs():
    "Output the current configuration"
    config = Config()
    for key in dir(config):
        if not key.startswith("__"):
            click.echo(f"{key}: {getattr(config, key)}")


@cli.command()
def version():
    "Output the current hash version based"
    config = Config()
    today = date.today()
    repo = Repo(".")

    elements = [str(today.year), f"{today.month:02}"]
    if config.use_day:
        elements.append(f"{today.day:02}")
    elements.append(str(repo.heads.master.commit)[: config.hash_length])

    version = "-".join(elements)
    click.echo(version)
