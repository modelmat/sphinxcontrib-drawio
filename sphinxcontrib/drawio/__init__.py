import os
import os.path
import platform
import subprocess
from hashlib import sha1
from pathlib import Path
from subprocess import Popen, PIPE
from tempfile import TemporaryFile
from time import sleep
from typing import Dict, Any, List

from docutils.nodes import Node, image as docutils_image
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.images import Image
from sphinx.application import Sphinx
from sphinx.builders import Builder
from sphinx.config import Config, ENUM
from sphinx.directives.patches import Figure
from sphinx.errors import SphinxError
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective
from sphinx.util.fileutil import copy_asset

from .deprecated import (DrawIONode, DrawIO,
                         render_drawio_html, render_drawio_latex)


__version__ = "0.0.12"

logger = logging.getLogger(__name__)

VALID_OUTPUT_FORMATS = ("png", "jpg", "svg", "pdf")


def is_headless(config: Config):
    if config.drawio_headless == "auto":
        if platform.system() != "Linux":
            # Xvfb can only run on Linux
            return False
        # DISPLAY will exist if an X-server is running
        return False if os.getenv("DISPLAY") else True
    elif isinstance(config.drawio_headless, bool):
        return config.drawio_headless
    # We should never reach this point as Sphinx ensures the config options


class DrawIOError(SphinxError):
    category = 'DrawIO Error'


def format_spec(argument: Any) -> str:
    return directives.choice(argument, VALID_OUTPUT_FORMATS)


def boolean_spec(argument: Any) -> bool:
    if argument == "true":
        return True
    elif argument == "false":
        return False
    else:
        raise ValueError("unexpected value. true or false expected")


def traverse(nodes):
  for node in nodes:
    yield node
    yield from traverse(node.children)


class DrawIOBase(SphinxDirective):
    option_spec = {
        "format": format_spec,
        "page-index": directives.nonnegative_int,
        "transparency":  boolean_spec,
        "export-scale":  directives.positive_int,
        "export-width":  directives.positive_int,
        "export-height":  directives.positive_int,
    }

    def run(self) -> List[Node]:
        rel_filename, filename = self.env.relfn2path(self.arguments[0])
        self.env.note_dependency(rel_filename)
        if not os.path.exists(filename):
            return [self.state.document.reporter.warning(
                "External draw.io file {} not found.".format(filename),
                lineno=self.lineno
            )]
        builder = self.env.app.builder
        builder_export_format = builder.config.drawio_builder_export_format
        try:
            export_format = builder_export_format[builder.name]
        except KeyError:
            logger.warning(f"No export format specified for builder "
                           f"'{builder.name}' in "
                           f"'drawio_builder_export_format'. Using "
                           f"'{FALLBACK_EXPORT_FORMAT}' as a fall-back.")
            export_format = FALLBACK_EXPORT_FORMAT
        export_relpath = drawio_export(builder, self.options, filename,
                                       export_format)
        nodes = super().run()
        for node in traverse(nodes):
            if isinstance(node, docutils_image):
                image = node
                break
        image["classes"].append("drawio")
        image["uri"] = '/' + str(export_relpath)
        return nodes


class DrawIOImage(DrawIOBase, Image):
    option_spec = Image.option_spec.copy()
    option_spec.update(DrawIOBase.option_spec)


class DrawIOFigure(DrawIOBase, Figure):
    option_spec = Figure.option_spec.copy()
    option_spec.update(DrawIOBase.option_spec)


OPTIONAL_UNIQUES = {
    "export-height": "height",
    "export-width": "width",
}


def drawio_export(builder: Builder, options: dict, in_filename: str,
                  default_output_format: str) -> str:
    """Render drawio file into an output image file."""

    page_index = str(options.get("page-index", 0))
    output_format = options.get("format") or default_output_format
    scale = str(options.get("export-scale",
                            builder.config.drawio_default_export_scale) / 100)
    transparent = options.get("transparency",
                              builder.config.drawio_default_transparency)
    no_sandbox = builder.config.drawio_no_sandbox

    input_abspath = Path(in_filename)
    input_relpath = input_abspath.relative_to(builder.srcdir)
    input_stem = input_abspath.stem

    # Any directive options which would change the output file would go here
    unique_values = (
        # This ensures that the same file hash is generated no matter the build directory
        # Mainly useful for pytest, as it creates a new build directory every time
        str(input_relpath),
        page_index,
        scale,
        "true" if transparent else "false",
        *[str(options.get(option)) for option in OPTIONAL_UNIQUES]
    )
    hash_key = "\n".join(unique_values)
    sha_key = sha1(hash_key.encode()).hexdigest()
    filename = Path(input_stem).with_suffix('.' + output_format)
    export_relpath = Path(".drawio") / sha_key / filename
    export_abspath = Path(builder.srcdir) / export_relpath
    export_abspath.parent.mkdir(parents=True, exist_ok=True)

    if (export_abspath.exists()
            and export_abspath.stat().st_mtime > input_abspath.stat().st_mtime):
        return export_relpath

    if builder.config.drawio_binary_path:
        binary_path = builder.config.drawio_binary_path
    elif platform.system() == "Windows":
        binary_path = r"C:\Program Files\draw.io\draw.io.exe"
    else:
        binary_path = "/opt/draw.io/drawio"

    scale_args = ["--scale", scale]
    if output_format == "pdf" and float(scale) == 1.0:
        # https://github.com/jgraph/drawio-desktop/issues/344 workaround
        scale_args.clear()

    extra_args = []
    for option, drawio_arg in OPTIONAL_UNIQUES.items():
        if option in options:
            value = options[option]
            extra_args.append("--{}".format(drawio_arg))
            extra_args.append(str(value))

    if transparent:
        extra_args.append("--transparent")

    drawio_args = [
        binary_path,
        "--export",
        "--crop",
        "--page-index",
        page_index,
        *scale_args,
        *extra_args,
        "--format",
        output_format,
        "--output",
        str(export_abspath),
        in_filename,
    ]

    if no_sandbox:
        # This may be needed for docker support, and it has to be the last argument to work.
        drawio_args.append("--no-sandbox")

    new_env = os.environ.copy()
    if builder.config._display:
        new_env["DISPLAY"] = ":{}".format(builder.config._display)

    try:
        ret = subprocess.run(drawio_args, stderr=PIPE, stdout=PIPE,
                             check=True, env=new_env)
        if not export_abspath.exists():
            raise DrawIOError("draw.io did not produce an output file:"
                              "\n[stderr]\n{}\n[stdout]\n{}"
                              .format(ret.stderr, ret.stdout))
        logger.info(f"(drawio) '{input_relpath}' -> '{export_relpath}'")
        return export_relpath
    except OSError as exc:
        raise DrawIOError("draw.io ({}) exited with error:\n{}"
                          .format(" ".join(drawio_args), exc))
    except subprocess.CalledProcessError as exc:
        raise DrawIOError("draw.io ({}) exited with error:\n[stderr]\n{}"
                          "\n[stdout]\n{}".format(" ".join(drawio_args),
                                                  exc.stderr, exc.stdout))


def on_config_inited(app: Sphinx, config: Config) -> None:
    if is_headless(config):
        logger.info("running in headless mode, starting Xvfb")
        with TemporaryFile() as fp:
            fd = fp.fileno()
            xvfb = Popen(["Xvfb", "-displayfd", str(fd), "-screen",
                          "0", "1280x768x16"], pass_fds=(fd, ),
                         stdout=PIPE, stderr=PIPE)
            if xvfb.poll() is not None:
                raise OSError("Failed to start Xvfb process"
                              "\n[stdout]\n{}\n[stderr]{}"
                              .format(*xvfb.communicate()))
            while fp.tell() == 0:
                sleep(0.01)   # wait for Xvfb to start up
            fp.seek(0)
            config._xvfb = xvfb
            config._display = fp.read().decode('ascii').strip()
        logger.info("Xvfb is running on display :{}".format(config._display))
    else:
        logger.info("running in non-headless mode, not starting Xvfb")
        config._xvfb = None
        config._display = None


def on_build_finished(app: Sphinx, exc: Exception) -> None:
    if exc is None:
        this_file_path = os.path.dirname(os.path.realpath(__file__))
        src = os.path.join(this_file_path, "drawio.css")
        dst = os.path.join(app.outdir, "_static")
        copy_asset(src, dst)

    if app.config._xvfb:
        app.config._xvfb.terminate()
        stdout, stderr = app.config._xvfb.communicate()
        if app.config._xvfb.poll() != 0:
            raise OSError("Encountered an issue while terminating Xvfb"
                          "\n[stdout]\n{}\n[stderr]{}".format(stdout, stderr))


FALLBACK_EXPORT_FORMAT = "png"
DEFAULT_BUILDER_EXPORT_FORMAT = {
    "html": "svg",
    "latex": "pdf",
    "rinoh": "pdf",
}


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_directive("drawio-image", DrawIOImage)
    app.add_directive("drawio-figure", DrawIOFigure)
    app.add_config_value("drawio_builder_export_format",
                         DEFAULT_BUILDER_EXPORT_FORMAT, "html", dict)
    app.add_config_value("drawio_default_export_scale", 100, "html")
    # noinspection PyTypeChecker
    app.add_config_value("drawio_default_transparency", False, "html",
                         ENUM(True, False))
    app.add_config_value("drawio_binary_path", None, "html")
    # noinspection PyTypeChecker
    app.add_config_value("drawio_headless", "auto", "html",
                         ENUM("auto", True, False))
    # noinspection PyTypeChecker
    app.add_config_value("drawio_no_sandbox", False, "html",
                         ENUM(True, False))

    # deprecated
    app.add_node(DrawIONode,
                 html=(render_drawio_html, None),
                 latex=(render_drawio_latex, None))
    app.add_directive("drawio", DrawIO)
    app.add_config_value("drawio_output_format", "png", "html", ENUM(*VALID_OUTPUT_FORMATS))
    app.add_config_value("drawio_default_scale", 1, "html")

    # Add CSS file to the HTML static path for add_css_file
    app.connect("build-finished", on_build_finished)
    app.connect("config-inited", on_config_inited)
    app.add_css_file("drawio.css")

    return {"version": __version__, "parallel_read_safe": True}
