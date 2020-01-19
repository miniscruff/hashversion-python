from hashversion.cli import Config


def fake_config(data):
    c = Config()
    c._config(data)
    return c
