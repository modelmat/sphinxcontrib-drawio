import pytest


@pytest.mark.sphinx("latex", testroot="simple")
def test_simple(tex: str):
    assert r"\sphinxincludegraphics[]" \
           r"{drawio-fb010705c7934a6a1d6bb9c92ad114cd0c2cac76.pdf}" in tex


@pytest.mark.sphinx("latex", testroot="align")
def test_align(tex: str):
    assert (r"{\sphinxincludegraphics[]{drawio-fb010705c7934a6a1d6bb9c92ad114cd0c2cac76.pdf}" "\n"
            r"\hspace*{\fill}}" "\n"
            r"{\hfill\sphinxincludegraphics[]{drawio-fb010705c7934a6a1d6bb9c92ad114cd0c2cac76.pdf}" "\n"
            r"\hspace*{\fill}}" "\n"
            r"{\hspace*{\fill}\sphinxincludegraphics[]{drawio-fb010705c7934a6a1d6bb9c92ad114cd0c2cac76.pdf}") in tex

