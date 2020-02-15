import pytest
from bs4 import BeautifulSoup

from sphinx.testing.path import path

pytest_plugins = "sphinx.testing.fixtures"


@pytest.fixture(scope="session")
def rootdir():
    return path(__file__).parent.abspath() / "roots"


@pytest.fixture()
def content(app):
    app.build()
    yield app


@pytest.fixture()
def page(content, request) -> BeautifulSoup:
    pagename = request.param
    c = (content.outdir / pagename).text()

    yield BeautifulSoup(c, "html.parser")
