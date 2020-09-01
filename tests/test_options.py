from pathlib import Path
from typing import List

import pytest

from bs4 import Tag
from sphinx.application import Sphinx
from sphinx.util.images import get_image_size


# deprecated drawio directive test
@pytest.mark.sphinx("html", testroot="simple")
def test_simple(directives: List[Tag]):
    assert directives[0].decode() == '<img alt="_images/drawio-bf0f85b68784bab0e62bf5902f5a46b65d71ee70.png" ' \
                                     'class="drawio" src="_images/drawio-bf0f85b68784bab0e62bf5902f5a46b65d71ee70.png' \
                                     '"/>'


@pytest.mark.sphinx("html", testroot="page-index")
def test_page_index(images: List[Path]):
    assert images[0].name == "pages.png"
    assert images[1].name == "pages1.png"
    assert images[2].name == "pages2.png"
    assert images[3].name == "pages.png"
    assert get_image_size(images[0]) == (124, 63)
    assert get_image_size(images[1]) == (64, 63)
    assert get_image_size(images[2]) == (64, 63)
    assert get_image_size(images[3]) == (124, 63)

    # deprecated drawio directive
    assert images[4].name == "drawio-23596e9713a51f864e734695324de3c19e930125.png"
    assert images[5].name == "drawio-d890782f09bf6478d353265d5894253de5fefbd3.png"
    assert images[6].name == "drawio-4d4e2f8704b20c01096eed9b97cd6588d479f3a6.png"
    assert images[7].name == "drawio-23596e9713a51f864e734695324de3c19e930125.png"
    assert get_image_size(images[4]) == (124, 63)
    assert get_image_size(images[5]) == (64, 63)
    assert get_image_size(images[6]) == (64, 63)
    assert get_image_size(images[7]) == (124, 63)


@pytest.mark.sphinx("html", testroot="alt")
def test_alt(directives: List[Tag]):
    assert directives[0]["alt"] == "An Example"

    # deprecated drawio directive
    assert directives[1]["alt"] == "An Example"


@pytest.mark.sphinx("html", testroot="align")
def test_align(directives: List[Tag]):
    assert "align-left" in directives[0]["class"]
    assert "align-center" in directives[1]["class"]
    assert "align-right" in directives[2]["class"]

    # deprecated drawio directive
    assert directives[3].parent.parent["align"] == "left"
    assert directives[4].parent.parent["align"] == "center"
    assert directives[5].parent.parent["align"] == "right"


# noinspection PyTypeChecker
@pytest.mark.sphinx("html", testroot="width-height")
def test_width_height(images: List[Path]):
    # https://github.com/jgraph/drawio-desktop/issues/254
    # Widths and heights are not exact

    assert get_image_size(images[0]) == (103, 53)
    assert get_image_size(images[1]) == (202, 102)
    assert get_image_size(images[2]) == (1007, 511)

    # deprecated drawio directive
    assert get_image_size(images[3]) == (103, 53)
    assert get_image_size(images[4]) == (202, 102)
    assert get_image_size(images[5]) == (1007, 511)


# noinspection PyTypeChecker
@pytest.mark.sphinx("html", testroot="scale")
def test_scale(images: List[Path]):
    # https://github.com/jgraph/drawio-desktop/issues/254
    # Scale is not exact

    # actual image size is 124x63
    assert get_image_size(images[0]) == (245, 124)
    assert get_image_size(images[1]) == (1217, 616)
    assert get_image_size(images[2]) == (64, 33)
    assert get_image_size(images[3]) == (124, 63)
    assert get_image_size(images[4]) == (610, 309)

    # deprecated drawio directive
    assert get_image_size(images[5]) == (245, 124)
    assert get_image_size(images[6]) == (1217, 616)
    assert get_image_size(images[7]) == (610, 309)


@pytest.mark.sphinx("html", testroot="transparency")
def test_transparency():
    pass


@pytest.mark.sphinx("html", testroot="image")
def test_image(directives: List[Tag]):
    img, = directives
    assert img.name == "img"
    assert img["src"] == "_images/box.svg"
    assert img["alt"] == "_images/box.svg"
    assert img["class"] == ["drawio"]


@pytest.mark.sphinx("html", testroot="figure")
def test_figure(content: Sphinx, directives: List[Tag]):
    filenames_sizes = [
        ("box.png", (124, 63)),
        ("box1.png", (185, 94)),
    ]
    for img, (filename, size) in zip(directives, filenames_sizes):
        assert img.name == "img"
        assert img["src"] == "_images/" + filename
        assert img["alt"] == "_images/" + filename
        assert img["class"] == ["drawio"]
        image_path = content.outdir / img["src"]
        assert get_image_size(image_path) == size
        div = img.parent
        assert div.name == 'div'
        assert "figure" in div["class"]


@pytest.mark.sphinx("html", testroot="reference")
def test_reference(directives: List[Tag]):
    img, = directives
    assert img.name == "img"
    assert img["src"] == "_images/box.svg"
    assert img["alt"] == "_images/box.svg"
    assert img["class"] == ["drawio"]


@pytest.mark.sphinx("html", testroot="warnings")
def test_warnings(content: Sphinx, directives: List[Tag]):
    assert len(directives) == 0
    warnings = content._warning.getvalue()
    assert "1 argument(s) required, 0 supplied" in warnings
    assert "missing.drawio not found" in warnings
