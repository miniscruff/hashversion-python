import click
from git import Repo
from datetime import date
import toml
import json
from secrets import token_hex
import os
from enum import Enum


class ExportSort(Enum):
    time = 0
    type = 1


class Config:
    def __init__(self):
        try:
            with open("pyproject.toml") as toml_file:
                toml_config = toml.load(toml_file)["tool"]["hashver"]
        except Exception as e:
            toml_config = {}

        self._config(toml_config)

    def _config(self, data):
        #: How many characters of the git hash to include.
        #: Defaults to 8, recommended 6-10 but anything is allowed
        self.hash_length = data.get("hash_length", 8)
        #: Whether or not to include a 2 digit day in your version
        self.use_day = data.get("use_day", False)
        #: Directory to store change files
        #: Defaults to changes
        self.change_directory = data.get("change_directory", "changes")
        #: What types of changes are allowed.
        #: Defaults to ones defined by keep a changelog
        self.change_types = data.get(
            "change_types",
            ["added", "changed", "deprecated", "removed", "fixed", "security"],
        )
        #: Extra questions to ask when generating change files
        self.extra_questions = data.get("extra_questions", {})
        #: File to export change logs to when using export
        #: Defaults to CHANGELOG.md
        self.export_file = data.get("export_file", "CHANGELOG.md")
        #: String format of exported changelogs"
        self.export_format = data.get(
            "export_format", "({year}-{month:02}-{day:02}) {type}: {description}\n"
        )
        #: How the exports are sorted, either time or type
        self.export_sort = ExportSort.__members__[data.get("export_sort", "time")]
        #: What to look for that starts the changelog in the export file.
        #: A line gap will automatically be added after your tag.
        #: Default: [Start Changelog]: # which acts as a markdown comment
        self.export_start = data.get("export_start", "[Start Changelog]: #")

        if not self.export_format.endswith("\n"):
            self.export_format += "\n"
        if not self.export_start.endswith("\n"):
            self.export_start += "\n"


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
        raise Exception(
            f'Invalid change type of "{data["type"]}" should be one of {config.change_types}'
        )

    data["year"] = today.year
    data["month"] = today.month
    data["day"] = today.day

    random_hex = token_hex()[:8]
    change_path = f"{config.change_directory}/{today.isoformat()}-{random_hex}.json"
    with open(change_path, "w") as change_file:
        json.dump(data, change_file, indent=2)


@cli.command()
def export():
    config = Config()
    if config.export_sort == ExportSort.time:
        sort_order = lambda data: (
            data["year"],
            data["month"],
            data["day"],
            -config.change_types.index(data["type"]),
        )
        reverse = True
    else:
        sort_order = lambda data: (
            config.change_types.index(data["type"]),
            -data["year"],
            -data["month"],
            -data["day"],
        )
        reverse = False

    changes = []
    for file in os.listdir(config.change_directory):
        if not file.endswith(".json"):
            continue
        change_path = os.path.join(config.change_directory, file)
        with open(change_path) as change_file:
            changes.append(json.load(change_file))

    if changes:
        try:
            file_lines = [
                line + "\n"
                for line in open(config.export_file).read().strip().split("\n")
            ]
        except FileNotFoundError:
            file_lines = []

        try:
            start_line = file_lines.index(config.export_start) + 2
        except ValueError:
            start_line = len(file_lines)

        # add a buffer line below our new changes
        if start_line > 0:
            file_lines.insert(start_line, "\n")
        for change_data in reversed(sorted(changes, key=sort_order, reverse=reverse)):
            file_lines.insert(start_line, config.export_format.format(**change_data))

        with open(config.export_file, "w") as changelog_file:
            changelog_file.writelines(file_lines)
