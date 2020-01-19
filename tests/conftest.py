import pytest
from click.testing import CliRunner


@pytest.fixture
def cli_runner():
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield runner
