from pathlib import Path
from typing import List

import pytest

from bs4 import Tag


@pytest.mark.sphinx("html", testroot="imgconverter")
def test_imgconverter(directives: List[Tag]):
    (img,) = directives
    assert img.name == "img"
    # This will have been converted from our exported
    # SVG to PNG by sphinx.ext.imgconverter
    assert img["src"] == "_images/box.png"
    assert img["alt"] == "_images/box.png"
    assert img["class"] == ["drawio"]
