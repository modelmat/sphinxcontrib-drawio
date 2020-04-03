import json
import os
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from sphinx.application import Sphinx

from sphinx.testing.path import path

pytest_plugins = "sphinx.testing.fixtures"


def _set_config_options_from_json(app: Sphinx, config: dict) -> None:
    for key, value in config.items():
        app.config[key] = value


def _set_config_options_from_json_path(app: Sphinx, config_path: str) -> None:
    """Adds extra sphinx conf.py values from a JSON file

    Equivalent to a conf.py inside the test root directory. Useful for
    having global config options between tests.

    Example:
    {
      "exclude_patterns": ["_build"],
      "drawio_headless": false
    }

    Modified from code by @yamionp
    """

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
            _set_config_options_from_json(app, config)

    except FileNotFoundError:
        pass


def _setup_local_user_config(app):
    """Sets the local user's conf.py values for all tests

    Useful for when a developer needs to configure values for a device-specific
    change. The file is .gitignore'd so it will not appear in git.
    Stored in tests/local_user_config.json"""
    local_user_conf_path = Path(__file__).parent.absolute() / "local_user_config.json"
    _set_config_options_from_json_path(app, local_user_conf_path)


def _setup_headless_mode_on_ci(app):
    """Enables drawio_headless=True when used in the CI environment

    Relies on the circleCI `CI` environment variable
    """
    if os.getenv("CI", False):
        _set_config_options_from_json(app, {"drawio_headless": True})


@pytest.fixture(scope="session")
def rootdir():
    return path(__file__).parent.abspath() / "roots"


@pytest.fixture()
def content(app: Sphinx):
    _setup_local_user_config(app)
    _setup_headless_mode_on_ci(app)
    app.build()
    yield app


@pytest.fixture()
def page(content: Sphinx, request) -> BeautifulSoup:
    page_name = request.param
    c = (content.outdir / page_name).text()

    yield BeautifulSoup(c, "html.parser")
