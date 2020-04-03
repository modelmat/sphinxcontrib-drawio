from typing import List

import pytest
from bs4 import BeautifulSoup, Tag


@pytest.mark.sphinx("html", testroot="page-index")
@pytest.mark.parametrize('page', ['index.html', ], indirect=True)
def test_page_index(page: BeautifulSoup):
    # noinspection PyTypeChecker
    directives: List[Tag] = page.find_all("img", {"class": "drawio"})

    assert directives[0]["src"] == "_images/drawio-6c599cfbc157f62547fc3354692ca5d80f5a1cbe.png"
    assert directives[1]["src"] == "_images/drawio-6af8a27a0319a0e5b9556732810e09f30031abed.png"
    assert directives[2]["src"] == "_images/drawio-2fe589eb5c844004225cf5a9a371867073a844ce.png"
    assert directives[3]["src"] == "_images/drawio-6c599cfbc157f62547fc3354692ca5d80f5a1cbe.png"
