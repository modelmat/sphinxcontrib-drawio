import pytest


@pytest.mark.sphinx("latex", testroot="simple")
def test_simple(tex: str):
    assert r"\sphinxincludegraphics[]" \
           r"{drawio-fb010705c7934a6a1d6bb9c92ad114cd0c2cac76.pdf}" in tex

