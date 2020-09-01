import re
from pathlib import Path
from typing import List

import pytest


# deprecated drawio directive test
@pytest.mark.sphinx("latex", testroot="simple", srcdir="pdf_simple")
def test_pdf_simple(legacy_tex_images: List[Path]):
    image, = legacy_tex_images
    assert image.basename() == "drawio-6cf867c6e94665d8489581a35c2d215220d6c152.pdf"


@pytest.mark.sphinx("latex", testroot="image", srcdir="pdf_image")
def test_pdf_image(tex_images: List[Path]):
    image, = tex_images
    assert image.basename() == "box.pdf"


# deprecated drawio directive test
@pytest.mark.sphinx("latex", testroot="simple", srcdir="pdf_crop")
def test_pdf_crop(legacy_tex_images: List[Path]):
    image, = legacy_tex_images
    assert get_mediabox(image) == ("88.080002", "46.079998")


@pytest.mark.sphinx("latex", testroot="image", srcdir="pdf_image_crop")
def test_pdf_image_crop(tex_images: List[Path]):
    image, = tex_images
    assert get_mediabox(image) == ("88.080002", "46.079998")


RE_MEDIABOX = re.compile(rb"^/MediaBox \[0 0 ([\d.]+) ([\d.]+)\]")


def get_mediabox(filename):
    with filename.open("rb") as pdf:
        for line in pdf.readlines():
            m = RE_MEDIABOX.match(line)
            if m:
                break
        else:
            assert False, "Could not find MediaBox in exported PDF"
    return tuple(g.decode("ascii") for g in m.groups())
