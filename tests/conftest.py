import json
import os

import pytest
from bs4 import BeautifulSoup

from sphinx.testing.path import path

pytest_plugins = "sphinx.testing.fixtures"


def _set_localconf(app):
    """
    Load additional configuration for local environment

    example: roots/test-root/localconf.json
    {
      "drawio_binary_path": "/Applications/draw.io.app/Contents/MacOS/draw.io",
      "drawio_headless": false
    }
    """

    local_conf_path = os.path.join(
        app.srcdir,
        'localconf.json',
    )

    try:
        with open(local_conf_path, 'r') as f:
            conf = json.load(f)
            for key, value in conf.items():
                app.config[key] = value

    except FileNotFoundError:
        pass


@pytest.fixture(scope="session")
def rootdir():
    return path(__file__).parent.abspath() / "roots"


@pytest.fixture()
def content(app):
    _set_localconf(app)
    app.build()
    yield app


@pytest.fixture()
def page(content, request) -> BeautifulSoup:
    pagename = request.param
    c = (content.outdir / pagename).text()

    yield BeautifulSoup(c, "html.parser")
