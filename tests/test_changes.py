from hashversion.cli import Config, cli
from tests.utils import fake_config
from unittest.mock import patch, MagicMock, DEFAULT
from datetime import date
import os
import json
import pytest


class TestCreateChanges:
    def invoke_change(self, cli_runner, input, **configs):
        with patch.multiple(
            "hashversion.cli", click=DEFAULT, Config=DEFAULT, date=DEFAULT
        ) as mocks:
            mocks["Config"].return_value = fake_config(configs)
            mocks["date"].today.return_value = date(year=2020, month=2, day=14)
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
                "date": "2020-02-14",
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
                "date": "2020-02-14",
                "type": "added",
                "description": "add a thing",
                "issue_key": "145",
            }


class TestExportChangelog:
    def invoke_export(self, cli_runner, **configs):
        with patch.multiple("hashversion.cli", click=DEFAULT, Config=DEFAULT) as mocks:
            mocks["Config"].return_value = fake_config(configs)
            result = cli_runner.invoke(cli, "export", catch_exceptions=False)
            print(result.stdout)

    def create_dummy_change(self):
        os.mkdir("changes")
        with open("changes/demo_change.json", "w") as change_file:
            json.dump(
                {"date": "2020-02-14", "type": "added", "description": "add a thing"},
                change_file,
            )

    def test_export_no_changes_no_changelog(self, cli_runner):
        with open("CHANGELOG.md", "w") as changelog_file:
            changelog_file.write("left alone")

        os.mkdir("changes")
        with open("changes/.keep", "w") as keep_file:
            keep_file.write("ignored")

        self.invoke_export(cli_runner)

        with open("CHANGELOG.md") as changelog_file:
            assert changelog_file.read() == "left alone"

    def test_export_to_empty_file_sorted_by_date(self, cli_runner):
        self.create_dummy_change()
        with open("changes/demo_change2.json", "w") as change_file:
            json.dump(
                {"date": "2020-02-13", "type": "fixed", "description": "fixed a thing"},
                change_file,
            )

        self.invoke_export(cli_runner)

        with open("CHANGELOG.md") as changelog_file:
            assert changelog_file.read() == (
                "* (2020-02-14) added: add a thing\n"
                "* (2020-02-13) fixed: fixed a thing\n"
            )

    def test_export_to_empty_file_sorted_by_type(self, cli_runner):
        self.create_dummy_change()
        with open("changes/demo_change2.json", "w") as change_file:
            json.dump(
                {"date": "2020-02-15", "type": "fixed", "description": "fixed a thing"},
                change_file,
            )

        self.invoke_export(cli_runner, export_sort="type")

        with open("CHANGELOG.md") as changelog_file:
            assert changelog_file.read() == (
                "* (2020-02-14) added: add a thing\n"
                "* (2020-02-15) fixed: fixed a thing\n"
            )

    def test_export_to_empty_file_with_complicated_date_sort(self, cli_runner):
        os.mkdir("changes")
        base_change = {"date": "2020-02-10", "type": "", "description": "desc"}
        with open("changes/demo_add.json", "w") as change_file:
            json.dump({**base_change, **{"type": "added"}}, change_file)
        with open("changes/demo_fixed.json", "w") as change_file:
            json.dump({**base_change, **{"type": "fixed"}}, change_file)
        with open("changes/demo_dep.json", "w") as change_file:
            json.dump({**base_change, **{"type": "deprecated"}}, change_file)
        with open("changes/demo_11.json", "w") as change_file:
            json.dump(
                {**base_change, **{"type": "added", "date": "2020-02-11"}}, change_file
            )

        self.invoke_export(cli_runner)

        with open("CHANGELOG.md") as changelog_file:
            assert changelog_file.read() == (
                "* (2020-02-11) added: desc\n"
                "* (2020-02-10) added: desc\n"
                "* (2020-02-10) deprecated: desc\n"
                "* (2020-02-10) fixed: desc\n"
            )

    def test_export_to_empty_file_with_complicated_type_sort(self, cli_runner):
        os.mkdir("changes")
        base_change = {"date": "2020-02-10", "type": "", "description": "desc"}
        with open("changes/demo_add.json", "w") as change_file:
            json.dump({**base_change, **{"type": "added"}}, change_file)
        with open("changes/demo_fixed.json", "w") as change_file:
            json.dump({**base_change, **{"type": "fixed"}}, change_file)
        with open("changes/demo_fix_11.json", "w") as change_file:
            json.dump(
                {**base_change, **{"type": "fixed", "date": "2020-02-11"}}, change_file
            )
        with open("changes/demo_fix_12.json", "w") as change_file:
            json.dump(
                {**base_change, **{"type": "fixed", "date": "2020-02-12"}}, change_file
            )
        with open("changes/demo_dep.json", "w") as change_file:
            json.dump({**base_change, **{"type": "deprecated"}}, change_file)
        with open("changes/demo_dep_11.json", "w") as change_file:
            json.dump(
                {**base_change, **{"type": "deprecated", "date": "2020-02-11"}},
                change_file,
            )

        self.invoke_export(cli_runner, export_sort="type")

        with open("CHANGELOG.md") as changelog_file:
            assert changelog_file.read() == (
                "* (2020-02-10) added: desc\n"
                "* (2020-02-11) deprecated: desc\n"
                "* (2020-02-10) deprecated: desc\n"
                "* (2020-02-12) fixed: desc\n"
                "* (2020-02-11) fixed: desc\n"
                "* (2020-02-10) fixed: desc\n"
            )

    def test_with_headers(self, cli_runner):
        os.mkdir("changes")
        base_change = {"date": "2020-04-10", "type": "added", "description": "desc"}
        with open("changes/demo_year.json", "w") as change_file:
            json.dump(base_change, change_file)
        with open("changes/demo_month.json", "w") as change_file:
            json.dump({**base_change, **{"date": "2020-03-10"}}, change_file)
        with open("changes/demo_day.json", "w") as change_file:
            json.dump({**base_change, **{"date": "2020-02-12"}}, change_file)
        with open("changes/demo_day_2.json", "w") as change_file:
            json.dump({**base_change, **{"date": "2020-02-13"}}, change_file)
        with open("changes/demo_month_2.json", "w") as change_file:
            json.dump({**base_change, **{"date": "2020-01-12"}}, change_file)

        self.invoke_export(
            cli_runner,
            year_header="# {date.year}",
            month_header="## {date.month}",
            day_header="### {date.day}",
        )

        with open("CHANGELOG.md") as changelog_file:
            assert changelog_file.read() == (
                "# 2020\n"
                "## 4\n"
                "### 10\n"
                "* (2020-04-10) added: desc\n"
                "## 3\n"
                "### 10\n"
                "* (2020-03-10) added: desc\n"
                "## 2\n"
                "### 13\n"
                "* (2020-02-13) added: desc\n"
                "### 12\n"
                "* (2020-02-12) added: desc\n"
                "## 1\n"
                "### 12\n"
                "* (2020-01-12) added: desc\n"
            )

    def test_with_month_name_day_of_week_name_header(self, cli_runner):
        os.mkdir("changes")
        base_change = {"date": "2020-01-20", "type": "added", "description": "desc"}
        with open("changes/demo_add.json", "w") as change_file:
            json.dump(base_change, change_file)

        self.invoke_export(
            cli_runner,
            year_header="# {date.year}",
            month_header="## {month_name}",
            day_header="### {day_name}",
        )

        with open("CHANGELOG.md") as changelog_file:
            assert changelog_file.read() == (
                "# 2020\n## January\n### Monday\n* (2020-01-20) added: desc\n"
            )

    def test_export_with_f_string_feature(self, cli_runner):
        os.mkdir("changes")
        with open("changes/demo_change.json", "w") as change_file:
            json.dump(
                {"date": "2020-02-14", "type": "added", "description": "add a thing"},
                change_file,
            )

        custom_format = "{type.title()}: {description}"
        self.invoke_export(cli_runner, export_format=custom_format)

        with open("CHANGELOG.md") as changelog_file:
            assert changelog_file.read() == ("Added: add a thing\n")

    def test_export_custom_format(self, cli_runner):
        os.mkdir("changes")
        with open("changes/demo_change.json", "w") as change_file:
            json.dump(
                {
                    "date": "2020-02-14",
                    "type": "added",
                    "description": "add a thing",
                    "issue_key": "1234",
                },
                change_file,
            )

        custom_format = (
            "[{issue_key}](github.com/issues/{issue_key}) **{type}**: {description}"
        )
        self.invoke_export(cli_runner, export_format=custom_format)

        with open("CHANGELOG.md") as changelog_file:
            assert changelog_file.read() == (
                "[1234](github.com/issues/1234) **added**: add a thing\n"
            )

    def test_export_different_file(self, cli_runner):
        self.create_dummy_change()
        self.invoke_export(cli_runner, export_file="HISTORY.md")

        with open("HISTORY.md") as changelog_file:
            assert changelog_file.read() != ""

    def test_export_keeps_header(self, cli_runner):
        with open("CHANGELOG.md", "w") as changelog_file:
            changelog_file.write("# Just a header\n")
            changelog_file.write("And some text\n")
            changelog_file.write("\n")
            changelog_file.write("[Start Changelog]: #\n")
            changelog_file.write("\n")
            changelog_file.write("End with me\n")

        self.create_dummy_change()
        self.invoke_export(cli_runner)

        with open("CHANGELOG.md") as changelog_file:
            assert changelog_file.read().split("\n") == [
                "# Just a header",
                "And some text",
                "",
                "[Start Changelog]: #",
                "",
                "* (2020-02-14) added: add a thing",
                "",
                "End with me",
                "",
            ]

    def test_export_custom_start(self, cli_runner):
        with open("CHANGELOG.md", "w") as changelog_file:
            changelog_file.write("# Just a header\n")
            changelog_file.write("And some text\n")
            changelog_file.write("\n")
            changelog_file.write("[DO NOT EDIT BELOW]: #\n")
            changelog_file.write("\n")
            changelog_file.write("End with me\n")

        self.create_dummy_change()
        self.invoke_export(cli_runner, export_start="[DO NOT EDIT BELOW]: #\n")

        with open("CHANGELOG.md") as changelog_file:
            assert changelog_file.read().split("\n") == [
                "# Just a header",
                "And some text",
                "",
                "[DO NOT EDIT BELOW]: #",
                "",
                "* (2020-02-14) added: add a thing",
                "",
                "End with me",
                "",
            ]
