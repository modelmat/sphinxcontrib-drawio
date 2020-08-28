import json
import os
import re
from pathlib import Path
from typing import List

import pytest
from bs4 import BeautifulSoup, Tag
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

    **Note**: This will not work for the `drawio_headless` config option.

    Useful for when a developer needs to configure values for a device-specific
    change. The file is .gitignore'd so it will not appear in git.
    Stored in tests/local_user_config.json"""
    local_user_conf_path = Path(__file__).parent.absolute() / "local_user_config.json"
    _set_config_options_from_json_path(app, local_user_conf_path)


@pytest.fixture(scope="session")
def rootdir():
    return path(__file__).parent.abspath() / "roots"


@pytest.fixture()
def content(app: Sphinx):
    _setup_local_user_config(app)
    app.build()
    yield app

    
@pytest.fixture()
def make_app_with_local_user_config(make_app):
    def make(*args, **kwargs):
        app = make_app(*args, **kwargs)
        _setup_local_user_config(app)
        return app

    yield make


def _directives(content: Sphinx) -> List[Tag]:
    c = (content.outdir / "index.html").read_text()
    return BeautifulSoup(c, "html.parser").find_all("img", {"class": "drawio"})


@pytest.fixture()
def directives(content: Sphinx) -> List[Tag]:
    return _directives(content)


@pytest.fixture()
def images(content: Sphinx) -> List[Path]:
    return [Path(content.outdir / tag["src"]) for tag in _directives(content)]


@pytest.fixture()
def legacy_tex_images(content: Sphinx) -> List[Path]:
    tex = (content.outdir / "python.tex").text()
    matches = re.finditer(r"\\sphinxincludegraphics\[\]{(.*?)}", tex)
    return [content.outdir / m.group(1) for m in matches]


@pytest.fixture()
def tex_images(content: Sphinx) -> List[Path]:
    tex = (content.outdir / "python.tex").text()
    matches = re.finditer(r"\\sphinxincludegraphics{{(.*)}\.pdf}", tex)
    return [content.outdir / (m.group(1) + '.pdf') for m in matches]


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "sphinx"
    )
