from pathlib import Path
from typing import List

import pytest
from bs4 import Tag
from sphinx.util.images import get_image_size


@pytest.mark.sphinx("html", testroot="simple")
def test_simple(directives: List[Tag]):
    assert directives[0].decode() == '<img alt="_images/drawio-fbceb72618f948b0bfc28d7a079cf11c81b6f333.png" ' \
                                     'class="drawio" src="_images/drawio-fbceb72618f948b0bfc28d7a079cf11c81b6f333.png' \
                                     '"/>'


@pytest.mark.sphinx("html", testroot="page-index")
def test_page_index(images: List[Path]):
    assert images[0].name == "drawio-c88b9718b7745fa0133283899fe862196cf2a708.png"
    assert images[1].name == "drawio-e38354aacbe9e35dd0777a43a55cd9ae100f85fe.png"
    assert images[2].name == "drawio-d570499ee2b0167a6033bb197f586999df37fe43.png"
    assert images[3].name == "drawio-c88b9718b7745fa0133283899fe862196cf2a708.png"


@pytest.mark.sphinx("html", testroot="alt")
def test_alt(directives: List[Tag]):
    assert directives[0]["alt"] == "An Example"


@pytest.mark.sphinx("html", testroot="align")
def test_align(directives: List[Tag]):
    assert directives[0].parent.parent["align"] == "left"
    assert directives[1].parent.parent["align"] == "center"
    assert directives[2].parent.parent["align"] == "right"


# noinspection PyTypeChecker
@pytest.mark.sphinx("html", testroot="width-height")
def test_width_height(images: List[Path]):
    # https://github.com/jgraph/drawio-desktop/issues/254
    # Widths and heights are not exact

    assert get_image_size(images[0]) == (103, 53)
    assert get_image_size(images[1]) == (202, 102)
    assert get_image_size(images[2]) == (1007, 511)

