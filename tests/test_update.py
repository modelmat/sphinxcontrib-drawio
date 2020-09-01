import shutil

from pathlib import Path

import pytest

from sphinx.application import Sphinx


SIMPLE_EXPORTED_FNAME = "drawio-bf0f85b68784bab0e62bf5902f5a46b65d71ee70.png"


# deprecated drawio directive test
@pytest.mark.sphinx("html", testroot="simple", srcdir="notchanged")
def test_notchanged(content: Sphinx, make_app_with_local_user_config):
    exported = content.outdir / "_images" / SIMPLE_EXPORTED_FNAME
    exported_timestamp = exported.stat().st_mtime
    app = make_app_with_local_user_config(srcdir=content.srcdir)
    app.build()
    assert exported.stat().st_mtime == exported_timestamp


# deprecated drawio directive test
@pytest.mark.sphinx("html", testroot="simple", srcdir="changed")
def test_changed(content: Sphinx, make_app_with_local_user_config):
    source = Path(content.srcdir / "box.drawio")
    exported = content.outdir / "_images" / SIMPLE_EXPORTED_FNAME
    exported_timestamp = exported.stat().st_mtime
    source.touch()
    app = make_app_with_local_user_config(srcdir=content.srcdir)
    app.build()
    assert exported.stat().st_mtime > exported_timestamp


@pytest.mark.sphinx("html", testroot="image", srcdir="image_notchanged")
def test_image_notchanged(content: Sphinx, make_app_with_local_user_config):
    exported = content.outdir / "_images" / "box.svg"
    exported_timestamp = exported.stat().st_mtime
    app = make_app_with_local_user_config(srcdir=content.srcdir)
    app.build()
    assert exported.stat().st_mtime == exported_timestamp


@pytest.mark.sphinx("html", testroot="image", srcdir="image_changed")
def test_image_changed(content: Sphinx, make_app_with_local_user_config):
    box = Path(content.srcdir / "box.drawio")
    exported = content.outdir / "_images" / "box.svg"
    exported_timestamp = exported.stat().st_mtime
    circle = Path(content.srcdir / "circle.drawio")
    shutil.copy(circle, box)
    app = make_app_with_local_user_config(srcdir=content.srcdir)
    app.build()
    assert exported.stat().st_mtime > exported_timestamp
