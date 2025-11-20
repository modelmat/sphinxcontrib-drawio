import re
import sphinx
from pathlib import Path
from typing import List

import pytest


@pytest.mark.sphinx("latex", testroot="image", srcdir="pdf_image")
def test_pdf_image(tex_images: List[Path]):
    (image,) = tex_images
    if sphinx.version_info[:2] < (7, 2):
        assert image.basename() == "box.pdf"
    else:
        assert image.name == "box.pdf"


@pytest.mark.sphinx("latex", testroot="image", srcdir="pdf_image_crop")
def test_pdf_image_crop(drawio_version, tex_images: List[Path]):
    if drawio_version <= (20, 6, 2):
        mediabox_size = ("88.080002", "47.039997")
    else:
        mediabox_size = ("89.040001", "45.119999")
    (image,) = tex_images
    assert get_mediabox(image, drawio_version) == mediabox_size


def get_mediabox(filename, drawio_version):
    if drawio_version <= (20, 6, 2):
        RE_MEDIABOX = re.compile(rb"^/MediaBox \[0 0 ([\d.]+) ([\d.]+)\]")
    else:
        RE_MEDIABOX = re.compile(rb"^/MediaBox \[\s*0\s*0\s*([\d.]+) ([\d.]+)\s*\]")
    with filename.open("rb") as pdf:
        for line in pdf.readlines():
            m = RE_MEDIABOX.match(line)
            if m:
                break
        else:
            assert False, "Could not find MediaBox in exported PDF"
    return tuple(g.decode("ascii") for g in m.groups())
