from pathlib import Path

import pytest
from sphinx.application import Sphinx


SIMPLE_EXPORTED_FNAME = "drawio-bf0f85b68784bab0e62bf5902f5a46b65d71ee70.png"


@pytest.mark.sphinx("html", testroot="simple")
def test_notchanged(content: Sphinx):
    exported = content.outdir / "_images" / SIMPLE_EXPORTED_FNAME
    exported_timestamp = exported.stat().st_mtime
    content.build()
    assert exported.stat().st_mtime == exported_timestamp


@pytest.mark.sphinx("html", testroot="simple")
def test_changed(content: Sphinx):
    source = Path(content.srcdir / "box.drawio")
    exported = content.outdir / "_images" / SIMPLE_EXPORTED_FNAME
    exported_timestamp = exported.stat().st_mtime
    source.touch()
    content.build()
    assert exported.stat().st_mtime > exported_timestamp
