from hashversion.cli import Config, cli
from unittest.mock import patch


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
        with patch("hashversion.cli.click") as mock_click:
            cli_runner.invoke(cli, "configs")
        mock_click.echo.assert_any_call("hash_length: 8")
