from hashversion.cli import Config, cli
from unittest.mock import patch, MagicMock, DEFAULT

# just a bunch of numbers in a row for easy test cases
default_commit_hash = "".join(str(x) for x in range(34))


class TestVersion:
    def invoke_version(self, cli_runner, **configs):
        with patch.multiple(
            "hashversion.cli", click=DEFAULT, Repo=DEFAULT, date=DEFAULT, Config=DEFAULT
        ) as mocks:
            fake_config = Config()
            for k, v in configs.items():
                setattr(fake_config, k, v)
            mocks["Config"].return_value = fake_config
            mocks["Repo"].return_value = MagicMock(
                heads=MagicMock(master=MagicMock(commit=default_commit_hash))
            )
            mocks["date"].today.return_value = MagicMock(year=2020, month=2, day=14)
            cli_runner.invoke(cli, "version", catch_exceptions=False)
            return mocks["click"].echo.call_args.args[0]

    def test_default(self, cli_runner):
        assert self.invoke_version(cli_runner) == "2020-02-01234567"

    def test_hash_length(self, cli_runner):
        assert self.invoke_version(cli_runner, hash_length=12) == "2020-02-012345678910"

    def test_use_day(self, cli_runner):
        assert self.invoke_version(cli_runner, use_day=True) == "2020-02-14-01234567"
