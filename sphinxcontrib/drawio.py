import os.path
import platform
import posixpath
import subprocess
from hashlib import sha1
from typing import Dict, Any, List

from docutils import nodes
from docutils.nodes import Node
from docutils.parsers.rst import directives
from sphinx.application import Sphinx
from sphinx.config import Config, ENUM
from sphinx.errors import SphinxError
from sphinx.util import logging, ensuredir
from sphinx.util.docutils import SphinxDirective, SphinxTranslator
from sphinx.util.fileutil import copy_asset
from sphinx.writers.html import HTMLTranslator

logger = logging.getLogger(__name__)

VALID_OUTPUT_FORMATS = ("png", "jpg", "svg")
X_DISPLAY_NUMBER = 1


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
    category = 'DrawIO Error'


def align_spec(argument: Any) -> str:
    return directives.choice(argument, ("left", "center", "right"))


# noinspection PyPep8Naming
class DrawIONode(nodes.General, nodes.Inline, nodes.Element):
    pass


class DrawIO(SphinxDirective):
    has_content = False
    required_arguments = 1
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {
        "alt": directives.unchanged,
        "align": align_spec,
        "page-index": directives.nonnegative_int,
    }

    def run(self) -> List[Node]:
        if self.arguments:
            rel_filename, filename = self.env.relfn2path(self.arguments[0])
            self.env.note_dependency(rel_filename)
            if not os.path.exists(filename):
                return [self.state.document.reporter.warning(
                    "External draw.io file {} not found.".format(filename),
                    lineno=self.lineno
                )]

        else:
            return [self.state_machine.reporter.warning(
                "Ignoring 'drawio' directive without argument.",
                line=self.lineno,
            )]

        node = DrawIONode()
        node["filename"] = filename
        if "alt" in self.options:
            node["alt"] = self.options["alt"]
        if "align" in self.options:
            node["align"] = self.options["align"]
        if "page-index" in self.options:
            node["page-index"] = self.options["page-index"]

        node["doc_name"] = self.env.docname

        self.add_name(node)
        return [node]


def render_drawio(self: SphinxTranslator, node: DrawIONode, in_filename: str,
                  output_format: str) -> str:
    """Render drawio file into an output image file."""

    page_index = str(node.get("page-index", 0))

    # Any directive options which would change the output file would go here
    unique_values = (
        # This ensures that the same file hash is generated no matter the build directory
        # Mainly useful for pytest, as it creates a new build directory every time
        node["filename"].replace(self.builder.srcdir, ""),
        page_index,
    )
    hash_key = "\n".join(unique_values)
    sha_key = sha1(hash_key.encode()).hexdigest()
    filename = "drawio-{}.{}".format(sha_key, output_format)
    file_path = posixpath.join(self.builder.imgpath, filename)
    out_file_path = os.path.join(self.builder.outdir, self.builder.imagedir,
                                 filename)

    if os.path.isfile(out_file_path):
        return file_path

    ensuredir(os.path.dirname(out_file_path))

    if self.builder.config.drawio_binary_path:
        binary_path = self.builder.config.drawio_binary_path
    elif platform.system() == "Windows":
        binary_path = r"C:\Program Files\draw.io\draw.io.exe"
    else:
        binary_path = "/opt/draw.io/drawio"

    drawio_args = [
        binary_path,
        "--no-sandbox",
        "--export",
        "--page-index",
        page_index,
        "--format",
        output_format,
        "--output",
        out_file_path,
        in_filename,
    ]

    doc_name = node.get("doc_name", "index")
    cwd = os.path.dirname(os.path.join(self.builder.srcdir, doc_name))

    new_env = os.environ.copy()
    if is_headless(self.config):
        new_env["DISPLAY"] = ":{}".format(X_DISPLAY_NUMBER)

    try:
        ret = subprocess.run(drawio_args, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                             cwd=cwd, check=True, env=new_env)
        if not os.path.isfile(out_file_path):
            raise DrawIOError("draw.io did not produce an output file:"
                              "\n[stderr]\n{}\n[stdout]\n{}"
                              .format(ret.stderr, ret.stdout))
        return file_path
    except OSError as exc:
        raise DrawIOError("draw.io ({}) exited with error:\n{}"
                          .format(" ".join(drawio_args), exc))
    except subprocess.CalledProcessError as exc:
        raise DrawIOError("draw.io ({}) exited with error:\n[stderr]\n{}"
                          "\n[stdout]\n{}".format(" ".join(drawio_args),
                                                  exc.stderr, exc.stdout))


def render_drawio_html(self: HTMLTranslator, node: DrawIONode) -> None:
    output_format = self.builder.config.drawio_output_format
    filename = node["filename"]
    try:
        file_path = render_drawio(self, node, filename, output_format)
    except DrawIOError as e:
        logger.warning("drawio filename: {}: {}".format(filename, e))
        raise nodes.SkipNode

    alt = node.get("alt", file_path)
    if "align" in node:
        self.body.append('<div align="{0}" class="align-{0}">'.format(node["align"]))

    if output_format == "svg":
        self.body.append('<div class="drawio">')
        self.body.append('<object data="{}" type="image/svg+xml"'
                         'class="drawio">\n'.format(file_path))
        self.body.append('<p class="warning">{}</p>'.format(alt))
        self.body.append('</object></div>\n')
    else:
        self.body.append('<div class="drawio">')
        self.body.append('<img src="{}" alt="{}" class="drawio" />'
                         .format(file_path, alt))
        self.body.append('</div>')

    if "align" in node:
        self.body.append('</div>\n')

    raise nodes.SkipNode


def on_config_inited(app: Sphinx, config: Config) -> None:
    if is_headless(config):
        process = subprocess.Popen(["Xvfb", ":{}".format(X_DISPLAY_NUMBER), "-screen", "0", "1280x768x16"],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        config.xvfb_pid = process.pid

        if process.poll() is not None:
            raise OSError("Failed to start Xvfb process"
                          "\n[stdout]\n{}\n[stderr]{}".format(*process.communicate()))

    else:
        logger.info("running in non-headless mode, not starting Xvfb")


def on_build_finished(app: Sphinx, exc: Exception) -> None:
    if exc is None:
        this_file_path = os.path.dirname(os.path.realpath(__file__))
        src = os.path.join(this_file_path, "drawio.css")
        dst = os.path.join(app.outdir, "_static")
        copy_asset(src, dst)

    if is_headless(app.builder.config):
        try:
            subprocess.run(["kill", str(app.builder.config.xvfb_pid)],
                           stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                           check=True)
        except subprocess.CalledProcessError as exc:
            logger.warning("Failed to kill Xvfb:n[stderr]\n{}"
                           "\n[stdout]\n{}".format(exc.stderr, exc.stdout))


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_node(DrawIONode, html=(render_drawio_html, None))
    app.add_directive("drawio", DrawIO)
    app.add_config_value("drawio_output_format", "png", "html", ENUM(*VALID_OUTPUT_FORMATS))
    app.add_config_value("drawio_binary_path", None, "html")
    # noinspection PyTypeChecker
    app.add_config_value("drawio_headless", "auto", "html", ENUM("auto", True, False))

    # Add CSS file to the HTML static path for add_css_file
    app.connect("build-finished", on_build_finished)
    app.connect("config-inited", on_config_inited)
    app.add_css_file("drawio.css")

    return {"parallel_read_safe": True}
