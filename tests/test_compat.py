from pathlib import Path
from typing import List

import pytest
import sphinx

from bs4 import Tag

# This tests two things:
# - That it doesn't convert when unnecessary
# - That it doesn't error.


@pytest.mark.sphinx("latex", testroot="imgconverter")
def test_pdfnoconvert(tex_images: List[Path]):
    (image,) = tex_images
    # It should not convert a PDF into another format.
    if sphinx.version_info[:2] < (7, 2):
        assert image.basename() == "box.pdf"
    else:
        assert image.name == "box.pdf"


@pytest.mark.sphinx("html", testroot="imgconverter")
def test_noconvert(directives: List[Tag]):
    # it should not convert an SVG output from sphinx into another format
    (image,) = directives
    assert image["src"] == "_images/box.svg"
    assert image["alt"] == "_images/box.svg"
