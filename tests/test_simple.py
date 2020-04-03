import pytest
from bs4 import BeautifulSoup, Tag


@pytest.mark.sphinx("html", testroot="simple")
@pytest.mark.parametrize('page', ['index.html', ], indirect=True)
def test_simple(page: BeautifulSoup):
    # noinspection PyTypeChecker
    directive: Tag = page.find("img", {"class": "drawio"})
    assert directive["alt"] == "An Example"
    assert directive["src"] == "_images/drawio-e1064ed5cbe76b6317e81b0401c554d5c3904545.png"""
