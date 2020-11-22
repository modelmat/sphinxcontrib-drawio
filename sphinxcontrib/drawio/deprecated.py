import os.path
import platform
import posixpath
import subprocess
from hashlib import sha1
from os.path import getmtime
from typing import Any, List

from docutils import nodes
from docutils.nodes import Node
from docutils.parsers.rst import directives
from sphinx.config import Config
from sphinx.errors import SphinxError
from sphinx.util import logging, ensuredir
from sphinx.util.docutils import SphinxDirective, SphinxTranslator
from sphinx.writers.html import HTMLTranslator
from sphinx.writers.latex import LaTeXTranslator


__all__ = ["DrawIONode", "DrawIO", "render_drawio_html", "render_drawio_latex"]


logger = logging.getLogger(__name__)

VALID_OUTPUT_FORMATS = ("png", "jpg", "svg")


def is_headless(config: Config):
    if config.drawio_headless == "auto":
        if platform.system() != "Linux":
            # Xvfb can only run on Linux
            return False

        # DISPLAY will exist if an X-server is running.
        if os.getenv("DISPLAY"):
            return False
        else:
            return True

    elif isinstance(config.drawio_headless, bool):
        return config.drawio_headless

    # We should never reach this point as Sphinx ensures the config options


class DrawIOError(SphinxError):
    category = "DrawIO Error"


def align_spec(argument: Any) -> str:
    return directives.choice(argument, ("left", "center", "right"))


def format_spec(argument: Any) -> str:
    return directives.choice(argument, VALID_OUTPUT_FORMATS)


def boolean_spec(argument: Any) -> bool:
    if argument == "true":
        return True
    elif argument == "false":
        return False
    else:
        raise ValueError("unexpected value. true or false expected")


# noinspection PyPep8Naming
class DrawIONode(nodes.General, nodes.Element):
    pass


class DrawIO(SphinxDirective):
    has_content = False
    required_arguments = 1
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {
        "align": align_spec,
        "alt": directives.unchanged,
        "format": format_spec,
        "height": directives.positive_int,
        "page-index": directives.nonnegative_int,
        "scale": directives.positive_int,
        "transparency": boolean_spec,
        "width": directives.positive_int,
    }
    optional_uniques = ("height", "width")

    def run(self) -> List[Node]:
        if self.arguments:
            rel_filename, filename = self.env.relfn2path(self.arguments[0])
            self.env.note_dependency(rel_filename)
            if not os.path.exists(filename):
                return [
                    self.state.document.reporter.warning(
                        "External draw.io file {} not found.".format(filename),
                        lineno=self.lineno,
                    )
                ]

        else:
            return [
                self.state_machine.reporter.warning(
                    "Ignoring 'drawio' directive without argument.",
                    line=self.lineno,
                )
            ]

        node = DrawIONode()
        node["filename"] = filename
        node["config"] = self.options
        node["doc_name"] = self.env.docname

        self.add_name(node)
        return [
            node,
            self.state_machine.reporter.warning(
                "The 'drawio' directive is deprecated. Use the 'drawio-image'"
                " directive instead.",
                line=self.lineno,
            ),
        ]


def render_drawio(
    self: SphinxTranslator,
    node: DrawIONode,
    in_filename: str,
    default_output_format: str,
) -> str:
    """Render drawio file into an output image file."""

    page_index = str(node["config"].get("page-index", 0))
    output_format = node["config"].get("format") or default_output_format
    scale = str(node["config"].get("scale", self.config.drawio_default_scale))
    transparent = node["config"].get(
        "transparency", self.config.drawio_default_transparency
    )
    no_sandbox = self.config.drawio_no_sandbox

    # Any directive options which would change the output file would go here
    unique_values = (
        # This ensures that the same file hash is generated no matter the build directory
        # Mainly useful for pytest, as it creates a new build directory every time
        node["filename"].replace(self.builder.srcdir, ""),
        page_index,
        scale,
        output_format,
        *[str(node["config"].get(option)) for option in DrawIO.optional_uniques],
    )
    hash_key = "\n".join(unique_values)
    sha_key = sha1(hash_key.encode()).hexdigest()
    filename = "drawio-{}.{}".format(sha_key, default_output_format)
    file_path = posixpath.join(self.builder.imgpath, filename)
    out_file_path = os.path.join(self.builder.outdir, self.builder.imagedir, filename)

    if os.path.isfile(out_file_path) and getmtime(in_filename) < getmtime(
        out_file_path
    ):
        return file_path

    ensuredir(os.path.dirname(out_file_path))

    if self.builder.config.drawio_binary_path:
        binary_path = self.builder.config.drawio_binary_path
    elif platform.system() == "Windows":
        binary_path = r"C:\Program Files\draw.io\draw.io.exe"
    else:
        binary_path = "/opt/draw.io/drawio"

    scale_args = ["--scale", scale]
    if output_format == "pdf" and float(scale) == 1.0:
        # https://github.com/jgraph/drawio-desktop/issues/344 workaround
        scale_args.clear()

    extra_args = []
    for option in DrawIO.optional_uniques:
        if option in node["config"]:
            value = node["config"][option]
            extra_args.append("--{}".format(option))
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
        out_file_path,
        in_filename,
    ]

    if no_sandbox:
        # This may be needed for docker support, and it has to be the last argument to work.
        drawio_args.append("--no-sandbox")

    doc_name = node.get("doc_name", "index")
    cwd = os.path.dirname(os.path.join(self.builder.srcdir, doc_name))

    new_env = os.environ.copy()
    if self.config._display:
        new_env["DISPLAY"] = ":{}".format(self.config._display)

    try:
        ret = subprocess.run(
            drawio_args,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            cwd=cwd,
            check=True,
            env=new_env,
        )
        if not os.path.isfile(out_file_path):
            raise DrawIOError(
                "draw.io did not produce an output file:"
                "\n[stderr]\n{}\n[stdout]\n{}".format(ret.stderr, ret.stdout)
            )
        return file_path
    except OSError as exc:
        raise DrawIOError(
            "draw.io ({}) exited with error:\n{}".format(" ".join(drawio_args), exc)
        )
    except subprocess.CalledProcessError as exc:
        raise DrawIOError(
            "draw.io ({}) exited with error:\n[stderr]\n{}"
            "\n[stdout]\n{}".format(" ".join(drawio_args), exc.stderr, exc.stdout)
        )


def render_drawio_html(self: HTMLTranslator, node: DrawIONode) -> None:
    output_format = self.builder.config.drawio_output_format
    filename = node["filename"]
    try:
        file_path = render_drawio(self, node, filename, output_format)
    except DrawIOError as e:
        logger.warning("drawio filename: {}: {}".format(filename, e))
        raise nodes.SkipNode

    alt = node["config"].get("alt", file_path)
    if "align" in node["config"]:
        self.body.append(
            '<div align="{0}" class="align-{0}">'.format(node["config"]["align"])
        )

    if output_format == "svg":
        self.body.append('<div class="drawio">')
        self.body.append(
            '<object data="{}" type="image/svg+xml"'
            'class="drawio">\n'.format(file_path)
        )
        self.body.append('<p class="warning">{}</p>'.format(alt))
        self.body.append("</object></div>\n")
    else:
        self.body.append('<div class="drawio">')
        self.body.append(
            '<img src="{}" alt="{}" class="drawio" />'.format(file_path, alt)
        )
        self.body.append("</div>")

    if "align" in node["config"]:
        self.body.append("</div>\n")

    raise nodes.SkipNode


def render_drawio_latex(self: LaTeXTranslator, node: DrawIONode) -> None:
    filename = node["filename"]
    try:
        # Here we force a PDF output as LaTeX does not support (SVG) easily,
        # meaning we would have to remove support or use an inferior format
        # for the pdf output. PDF output also means that text and is more
        # natively integrated into the output PDF, at the cost of taking up a
        # full output page.
        # See also the implementation in sphinx's "graphviz" extension
        file_path = render_drawio(self, node, filename, "pdf")
    except DrawIOError as e:
        logger.warning("drawio filename: {}: {}".format(filename, e))
        raise nodes.SkipNode

    # TODO: Add :alt: support as PDF captions, if it doesn't interfere with output

    self.body.append(r"\sphinxincludegraphics[]{%s}" % file_path)

    raise nodes.SkipNode
