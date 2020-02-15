import pytest
from bs4 import BeautifulSoup, Tag


@pytest.mark.parametrize('page', ['index.html', ], indirect=True)
def test_index(page: BeautifulSoup):
    # noinspection PyTypeChecker
    directive: Tag = page.find("img", {"class": "drawio"})
    assert directive["alt"] == "An Example"
    assert directive["src"] == "_images/drawio-f0e5e78beadac41b11ee597d5d19874d3303cd74.png"""
