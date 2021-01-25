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

from docutils import nodes
from docutils.nodes import Node, image as docutils_image
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.images import Image
from sphinx.application import Sphinx
from sphinx.config import Config, ENUM
from sphinx.directives.patches import Figure
from sphinx.errors import SphinxError
from sphinx.transforms.post_transforms.images import ImageConverter, get_filename_for
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective
from sphinx.util.fileutil import copy_asset

from .deprecated import DrawIONode, DrawIO, render_drawio_html, render_drawio_latex


__version__ = "0.0.13"

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
    category = "DrawIO Error"


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
        "transparency": boolean_spec,
        "export-scale": directives.positive_int,
        "export-width": directives.positive_int,
        "export-height": directives.positive_int,
    }

    def run(self) -> List[Node]:
        nodes = super().run()
        for node in traverse(nodes):
            if isinstance(node, docutils_image):
                image = node
                break
        image["classes"].append("drawio")
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


class DrawIOConverter(ImageConverter):
    conversion_rules = [
        # automatic conversion based on the builder's supported image types
        ("application/x-drawio", "image/png"),
        ("application/x-drawio", "image/jpeg"),
        ("application/x-drawio", "image/svg+xml"),
        ("application/x-drawio", "application/pdf"),
        # when the export format is explicitly defined
        ("application/x-drawio-png", "image/png"),
        ("application/x-drawio-jpg", "image/jpeg"),
        ("application/x-drawio-svg", "image/svg+xml"),
        ("application/x-drawio-pdf", "application/pdf"),
    ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        builder_name = self.app.builder.name
        format = self.config.drawio_builder_export_format.get(builder_name)
        if format and format not in VALID_OUTPUT_FORMATS:
            raise DrawIOError(
                f"Invalid export format '{format}' specified for builder"
                f" '{builder_name}'"
            )
        self._default_export_format = format

    @property
    def imagedir(self) -> str:
        return os.path.join(self.app.doctreedir, "drawio")

    def is_available(self) -> bool:
        """Confirms the converter is available or not."""
        return True

    def guess_mimetypes(self, node: nodes.image) -> List[str]:
        if "drawio" in node["classes"]:
            format = node.get("format") or self._default_export_format
            extra = "-{}".format(format) if format else ""
            return ["application/x-drawio" + extra]
        return [None]

    def handle(self, node: nodes.image) -> None:
        """Render drawio file into an output image file."""
        _from, _to = self.get_conversion_rule(node)
        if _from in node["candidates"]:
            srcpath = node["candidates"][_from]
        else:
            srcpath = node["candidates"]["*"]

        abs_srcpath = Path(self.app.srcdir) / srcpath
        if not os.path.exists(abs_srcpath):
            return

        options = node.attributes
        out_filename = get_filename_for(srcpath, _to)
        destpath = self._drawio_export(abs_srcpath, options, out_filename)
        if "*" in node["candidates"]:
            node["candidates"]["*"] = destpath
        else:
            node["candidates"][_to] = destpath
        node["uri"] = destpath

        self.env.original_image_uri[destpath] = srcpath
        self.env.images.add_file(self.env.docname, destpath)

    def _drawio_export(self, input_abspath, options, out_filename):
        builder = self.app.builder
        input_relpath = input_abspath.relative_to(builder.srcdir)
        input_stem = input_abspath.stem

        page_index = str(options.get("page-index", 0))
        scale = str(
            options.get("export-scale", builder.config.drawio_default_export_scale)
            / 100
        )
        transparent = options.get(
            "transparency", builder.config.drawio_default_transparency
        )
        no_sandbox = builder.config.drawio_no_sandbox

        # Any directive options which would change the output file would go here
        unique_values = (
            # This ensures that the same file hash is generated no matter the build directory
            # Mainly useful for pytest, as it creates a new build directory every time
            str(input_relpath),
            page_index,
            scale,
            "true" if transparent else "false",
            *[str(options.get(option)) for option in OPTIONAL_UNIQUES],
        )
        hash_key = "\n".join(unique_values)
        sha_key = sha1(hash_key.encode()).hexdigest()
        export_abspath = Path(self.imagedir) / sha_key / out_filename
        export_abspath.parent.mkdir(parents=True, exist_ok=True)
        export_relpath = export_abspath.relative_to(builder.doctreedir)
        output_format = export_abspath.suffix[1:]

        if (
            export_abspath.exists()
            and export_abspath.stat().st_mtime > input_abspath.stat().st_mtime
        ):
            return export_abspath

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
            str(input_abspath),
        ]

        if no_sandbox:
            # This may be needed for docker support, and it has to be the last argument to work.
            drawio_args.append("--no-sandbox")

        new_env = os.environ.copy()
        if builder.config._display:
            new_env["DISPLAY"] = ":{}".format(builder.config._display)

        logger.info(f"(drawio) '{input_relpath}' -> '{export_relpath}'")
        try:
            ret = subprocess.run(
                drawio_args, stderr=PIPE, stdout=PIPE, check=True, env=new_env
            )
        except OSError as exc:
            raise DrawIOError(
                "draw.io ({}) exited with error:\n{}".format(" ".join(drawio_args), exc)
            )
        except subprocess.CalledProcessError as exc:
            raise DrawIOError(
                "draw.io ({}) exited with error:\n[stderr]\n{}"
                "\n[stdout]\n{}".format(" ".join(drawio_args), exc.stderr, exc.stdout)
            )
        if not export_abspath.exists():
            raise DrawIOError(
                "draw.io did not produce an output file:"
                "\n[stderr]\n{}\n[stdout]\n{}".format(ret.stderr, ret.stdout)
            )
        return export_abspath


def on_config_inited(app: Sphinx, config: Config) -> None:
    if is_headless(config):
        logger.info("running in headless mode, starting Xvfb")
        with TemporaryFile() as fp:
            fd = fp.fileno()
            xvfb = Popen(
                ["Xvfb", "-displayfd", str(fd), "-screen", "0", "1280x768x16"],
                pass_fds=(fd,),
                stdout=PIPE,
                stderr=PIPE,
            )
            if xvfb.poll() is not None:
                raise OSError(
                    "Failed to start Xvfb process"
                    "\n[stdout]\n{}\n[stderr]{}".format(*xvfb.communicate())
                )
            while fp.tell() == 0:
                sleep(0.01)  # wait for Xvfb to start up
            fp.seek(0)
            config._xvfb = xvfb
            config._display = fp.read().decode("ascii").strip()
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
            raise OSError(
                "Encountered an issue while terminating Xvfb"
                "\n[stdout]\n{}\n[stderr]{}".format(stdout, stderr)
            )


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_post_transform(DrawIOConverter)
    app.add_directive("drawio-image", DrawIOImage)
    app.add_directive("drawio-figure", DrawIOFigure)
    app.add_config_value("drawio_builder_export_format", {}, "html", dict)
    app.add_config_value("drawio_default_export_scale", 100, "html")
    # noinspection PyTypeChecker
    app.add_config_value(
        "drawio_default_transparency", False, "html", ENUM(True, False)
    )
    app.add_config_value("drawio_binary_path", None, "html")
    # noinspection PyTypeChecker
    app.add_config_value("drawio_headless", "auto", "html", ENUM("auto", True, False))
    # noinspection PyTypeChecker
    app.add_config_value("drawio_no_sandbox", False, "html", ENUM(True, False))

    # deprecated
    app.add_node(
        DrawIONode, html=(render_drawio_html, None), latex=(render_drawio_latex, None)
    )
    app.add_directive("drawio", DrawIO)
    app.add_config_value(
        "drawio_output_format", "png", "html", ENUM(*VALID_OUTPUT_FORMATS)
    )
    app.add_config_value("drawio_default_scale", 1, "html")

    # Add CSS file to the HTML static path for add_css_file
    app.connect("build-finished", on_build_finished)
    app.connect("config-inited", on_config_inited)
    app.add_css_file("drawio.css")

    return {"version": __version__, "parallel_read_safe": True}
