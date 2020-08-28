from pathlib import Path
from typing import List

import pytest
from bs4 import Tag
from sphinx.util.images import get_image_size


@pytest.mark.sphinx("html", testroot="simple")
def test_simple(directives: List[Tag]):
    assert directives[0].decode() == '<img alt="_images/drawio-bf0f85b68784bab0e62bf5902f5a46b65d71ee70.png" ' \
                                     'class="drawio" src="_images/drawio-bf0f85b68784bab0e62bf5902f5a46b65d71ee70.png' \
                                     '"/>'


@pytest.mark.sphinx("html", testroot="page-index")
def test_page_index(images: List[Path]):
    assert images[0].name == "drawio-23596e9713a51f864e734695324de3c19e930125.png"
    assert images[1].name == "drawio-d890782f09bf6478d353265d5894253de5fefbd3.png"
    assert images[2].name == "drawio-4d4e2f8704b20c01096eed9b97cd6588d479f3a6.png"
    assert images[3].name == "drawio-23596e9713a51f864e734695324de3c19e930125.png"
    
    assert get_image_size(images[0]) == (124, 63)
    assert get_image_size(images[1]) == (64, 63)
    assert get_image_size(images[2]) == (64, 63)
    assert get_image_size(images[3]) == (124, 63)


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


# noinspection PyTypeChecker
@pytest.mark.sphinx("html", testroot="scale")
def test_scale(images: List[Path]):
    # https://github.com/jgraph/drawio-desktop/issues/254
    # Scale is not exact

    # actual image size is 124x63
    assert get_image_size(images[0]) == (245, 124)
    assert get_image_size(images[1]) == (1217, 616)
    assert get_image_size(images[2]) == (610, 309)


@pytest.mark.sphinx("html", testroot="transparency")
def test_transparency():
    pass

