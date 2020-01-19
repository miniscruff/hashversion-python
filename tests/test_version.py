from hashver import Config, cli
from unittest.mock import patch, MagicMock, DEFAULT
import pytest


@pytest.fixture
def with_configs():
    with patch("hashver.Config") as mock_config:
        yield mock_config


class TestConfig:
    def test_use_defaults(self):
        c = Config()
        assert c.hash_length == 8

    def test_load_from_pyproject(self, cli_runner):
        with open("pyproject.toml", "w") as toml_file:
            toml_file.writelines(["[tool.hashver]\n", "hash_length = 12\n"])
        c = Config()
        assert c.hash_length == 12


class TestShowConfigs:
    def test_prints_data(self, cli_runner):
        with patch("click.echo") as mock_echo:
            cli_runner.invoke(cli, "configs")
        mock_echo.assert_any_call("hash_length: 8")


# just a bunch of numbers in a row for easy test cases
default_commit_hash = "".join(str(x) for x in range(34))


class TestVersion:
    def invoke_version(
        self,
        cli_runner,
        year=2020,
        month=2,
        day=14,
        commit=default_commit_hash,
        **configs
    ):
        with patch.multiple(
            "hashver", click=DEFAULT, Repo=DEFAULT, date=DEFAULT, Config=DEFAULT
        ) as mocks:
            fake_config = Config()
            for k, v in configs.items():
                setattr(fake_config, k, v)
            mocks["Config"].return_value = fake_config
            mocks["Repo"].return_value = MagicMock(
                heads=MagicMock(master=MagicMock(commit=commit))
            )
            mocks["date"].today.return_value = MagicMock(
                year=year, month=month, day=day
            )
            cli_runner.invoke(cli, "version", catch_exceptions=False)
            return mocks["click"].echo.call_args.args[0]

    def test_default(self, cli_runner):
        assert self.invoke_version(cli_runner) == "2020-02-01234567"

    def test_hash_length(self, cli_runner):
        assert self.invoke_version(cli_runner, hash_length=12) == "2020-02-012345678910"

    def test_use_day(self, cli_runner):
        assert self.invoke_version(cli_runner, use_day=True) == "2020-02-14-01234567"
