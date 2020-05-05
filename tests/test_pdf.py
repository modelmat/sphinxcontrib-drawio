import pytest


@pytest.mark.sphinx("latex", testroot="simple")
def test_simple(tex: str):
    assert r"\sphinxincludegraphics[]" \
           r"{drawio-6cf867c6e94665d8489581a35c2d215220d6c152.pdf}" in tex

