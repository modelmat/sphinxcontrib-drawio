import shutil

from pathlib import Path
from typing import List

import pytest

from sphinx.application import Sphinx


@pytest.mark.sphinx("latex", testroot="image", srcdir="image_latex_then_html")
def test_image_latex_then_html(
    content: Sphinx, tex_images: List[Path], make_app_with_local_user_config
):
    box_pdf = tex_images[0]
    assert box_pdf.basename() == "box.pdf"
    assert box_pdf.exists()
    html_app = make_app_with_local_user_config(srcdir=content.srcdir)
    html_app.build()
    box_svg = html_app.outdir / "_images" / "box.svg"
    assert box_svg.exists()
