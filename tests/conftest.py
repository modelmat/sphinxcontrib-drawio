import json
import os
import re
import platform
import subprocess
import sphinx
import shutil
from pathlib import Path
from typing import List
from time import sleep
from tempfile import TemporaryFile

import pytest
from bs4 import BeautifulSoup, Tag
from sphinx.application import Sphinx

pytest_plugins = "sphinx.testing.fixtures"


def _set_config_options_from_json(app: Sphinx, config: dict) -> None:
    for key, value in config.items():
        app.config[key] = value


def _set_config_options_from_json_path(app: Sphinx, config_path: str) -> None:
    """Adds extra sphinx conf.py values from a JSON file

    Equivalent to a conf.py inside the test root directory. Useful for
    having global config options between tests.

    Example:
    {
      "exclude_patterns": ["_build"],
      "drawio_headless": false
    }

    Modified from code by @yamionp
    """

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
            _set_config_options_from_json(app, config)

    except FileNotFoundError:
        pass


def _setup_local_user_config(app):
    """Sets the local user's conf.py values for all tests

    **Note**: This will not work for the `drawio_headless` config option.

    Useful for when a developer needs to configure values for a device-specific
    change. The file is .gitignore'd so it will not appear in git.
    Stored in tests/local_user_config.json"""
    local_user_conf_path = Path(__file__).parent.absolute() / "local_user_config.json"
    _set_config_options_from_json_path(app, local_user_conf_path)


@pytest.fixture(scope="session")
def rootdir():
    if sphinx.version_info[:2] < (7, 2):
        from sphinx.testing.path import path

        return path(__file__).parent.abspath() / "roots"

    return Path(__file__).resolve().parent / "roots"


@pytest.fixture(scope="session")
def drawio_version():
    def is_headless():
        if platform.system() != "Linux":
            # Xvfb can only run on Linux
            return False
        # DISPLAY will exist if an X-server is running
        return False if os.getenv("DISPLAY") else True

    def terminate_xvfb(xvfb: subprocess.Popen | None):
        if not xvfb:
            return
        xvfb.terminate()
        stdout, stderr = xvfb.communicate()
        if xvfb.poll() != 0:
            raise OSError(
                "Encountered an issue while terminating Xvfb"
                f"\n[stdout]\n{stdout}\n[stderr]{stderr}"
            )

    xvfb = None
    display = None
    if is_headless():
        with TemporaryFile() as fp:
            fd = fp.fileno()
            xvfb = subprocess.Popen(
                ["Xvfb", "-displayfd", str(fd), "-screen", "0", "1280x768x16"],
                pass_fds=(fd,),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if xvfb.poll() is not None:
                raise OSError(
                    "Failed to start Xvfb process\n[stdout]\n{}\n[stderr]{}".format(
                        *xvfb.communicate()
                    )
                )
            while fp.tell() == 0:
                sleep(0.01)  # wait for Xvfb to start up
            fp.seek(0)
            display = fp.read().decode("ascii").strip()
    env = os.environ.copy()
    if display:
        env["DISPLAY"] = f":{display}"
    # This environment variable prevents the drawio application from starting.
    # This is automatically set within certain Visual Studio Code contexts,
    # such as for the reStructuredText (sphinx) preview.
    env.pop("ELECTRON_RUN_AS_NODE", None)
    drawio = shutil.which("drawio") or shutil.which("draw.io")
    ret = subprocess.run(
        [drawio, "--version"],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        check=True,
        env=env,
    )
    out: str = ret.stdout.decode().strip()
    m = re.search(r"(\d{1,}\.\d{1,}\.\d{1,})", out)
    try:
        ver_str = m.group(1)
    except (IndexError, AttributeError):
        terminate_xvfb()
        raise SystemExit(out)
    try:
        version = tuple(int(i) for i in ver_str.split("."))
    except:
        terminate_xvfb()
        raise SystemExit(ver_str)
    return version


@pytest.fixture()
def app_with_local_user_config(app: Sphinx):
    _setup_local_user_config(app)
    yield app


@pytest.fixture()
def content(app_with_local_user_config: Sphinx):
    app_with_local_user_config.build()
    yield app_with_local_user_config


@pytest.fixture()
def make_app_with_local_user_config(make_app):
    def make(*args, **kwargs):
        app = make_app(*args, **kwargs)
        _setup_local_user_config(app)
        return app

    yield make


def _directives(content: Sphinx) -> List[Tag]:
    c = (content.outdir / "index.html").read_text()
    return BeautifulSoup(c, "html.parser").find_all("img", {"class": "drawio"})


@pytest.fixture()
def directives(content: Sphinx) -> List[Tag]:
    return _directives(content)


@pytest.fixture()
def images(content: Sphinx) -> List[Path]:
    return [Path(content.outdir / tag["src"]) for tag in _directives(content)]


@pytest.fixture()
def legacy_tex_images(content: Sphinx) -> List[Path]:
    tex = (content.outdir / "python.tex").read_text()
    matches = re.finditer(r"\\sphinxincludegraphics\[\]{(.*?)}", tex)
    return [content.outdir / m.group(1) for m in matches]


@pytest.fixture()
def tex_images(content: Sphinx) -> List[Path]:
    tex = (content.outdir / "python.tex").read_text()
    matches = re.finditer(r"\\sphinxincludegraphics{{(.*)}\.pdf}", tex)
    return [content.outdir / (m.group(1) + ".pdf") for m in matches]


def pytest_configure(config):
    config.addinivalue_line("markers", "sphinx")
