import click
from git import Repo
from datetime import date
import toml
import json
from secrets import token_hex


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
        #: Directory to store change files
        #: Defaults to changes
        self.change_directory = toml_config.get("change_directory", "changes")
        #: What types of changes are allowed.
        #: Defaults to ones defined by keep a changelog
        self.change_types = toml_config.get(
            "change_types",
            ["added", "changed", "deprecated", "removed", "fixed", "security"],
        )
        #: Extra questions to ask when generating change files
        self.extra_questions = toml_config.get("extra_questions", {})


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


@cli.command()
def change():
    "Create a change file by answering some questions"
    config = Config()
    today = date.today()

    # similar to cookie cutter
    # the keys are keys and values are input labels
    data = {
        "type": "Type of change?",
        "description": "Description of change",
        **config.extra_questions,
    }
    for question in data:
        data[question] = input(data[question] + ": ")

    if data["type"] not in config.change_types:
        raise Exception("Invalid change type of " + data["type"])

    data["year"] = today.year
    data["month"] = today.month
    data["day"] = today.day

    random_hex = token_hex()[:8]
    change_path = f"{config.change_directory}/{today.isoformat()}-{random_hex}.json"
    with open(change_path, "w") as change_file:
        json.dump(data, change_file)
