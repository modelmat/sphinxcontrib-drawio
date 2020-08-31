from pathlib import Path

import pytest
from sphinx.application import Sphinx


SIMPLE_EXPORTED_FNAME = "drawio-bf0f85b68784bab0e62bf5902f5a46b65d71ee70.png"


@pytest.mark.sphinx("html", testroot="simple")
def test_notchanged(content: Sphinx, make_app_with_local_user_config):
    exported = content.outdir / "_images" / SIMPLE_EXPORTED_FNAME
    exported_timestamp = exported.stat().st_mtime
    app = make_app_with_local_user_config(srcdir=content.srcdir)
    app.build()
    assert exported.stat().st_mtime == exported_timestamp


@pytest.mark.sphinx("html", testroot="simple")
def test_changed(content: Sphinx, make_app_with_local_user_config):
    source = Path(content.srcdir / "box.drawio")
    exported = content.outdir / "_images" / SIMPLE_EXPORTED_FNAME
    exported_timestamp = exported.stat().st_mtime
    source.touch()
    app = make_app_with_local_user_config(srcdir=content.srcdir)
    app.build()
    assert exported.stat().st_mtime > exported_timestamp
