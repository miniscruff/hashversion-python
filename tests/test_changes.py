from hashversion.cli import Config, cli
from unittest.mock import patch, MagicMock, DEFAULT
import os
import json
import pytest


class TestCreateChanges:
    def invoke_change(self, cli_runner, input, **configs):
        with patch.multiple(
            "hashversion.cli", click=DEFAULT, Config=DEFAULT, date=DEFAULT
        ) as mocks:
            fake_config = Config()
            for k, v in configs.items():
                setattr(fake_config, k, v)
            mocks["Config"].return_value = fake_config
            mocks["date"].today.return_value = MagicMock(year=2020, month=2, day=14)
            cli_runner.invoke(
                cli, "change", input="\n".join(input), catch_exceptions=False
            )

    def test_create_file(self, cli_runner):
        os.mkdir("changes")
        self.invoke_change(cli_runner, ["added", "add a thing"])
        files = os.listdir("changes")
        assert len(files) == 1
        with open("changes/" + files[0]) as change_file:
            assert json.load(change_file) == {
                "year": 2020,
                "month": 2,
                "day": 14,
                "type": "added",
                "description": "add a thing",
            }

    def test_error_on_invalid_type(self, cli_runner):
        os.mkdir("changes")
        with pytest.raises(Exception):
            self.invoke_change(cli_runner, ["not valid type", "add a thing"])

    def test_custom_change_types(self, cli_runner):
        os.mkdir("changes")
        self.invoke_change(
            cli_runner, ["unicorns", "unicorned"], change_types=["unicorns"]
        )
        files = os.listdir("changes")
        with open("changes/" + files[0]) as change_file:
            assert json.load(change_file)["type"] == "unicorns"

    def test_custom_change_folder(self, cli_runner):
        os.mkdir("history")
        self.invoke_change(cli_runner, ["added", "a thing"], change_directory="history")
        files = os.listdir("history")
        assert len(files) == 1

    def test_custom_questions(self, cli_runner):
        os.mkdir("changes")
        self.invoke_change(
            cli_runner,
            ["added", "add a thing", "145"],
            extra_questions={"issue_key": "Github Issue"},
        )
        files = os.listdir("changes")
        assert len(files) == 1
        with open("changes/" + files[0]) as change_file:
            assert json.load(change_file) == {
                "year": 2020,
                "month": 2,
                "day": 14,
                "type": "added",
                "description": "add a thing",
                "issue_key": "145",
            }


class TestUpdateChangelog:
    pass
