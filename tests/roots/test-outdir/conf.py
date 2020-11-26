import tempfile
import os

extensions = ["sphinxcontrib.drawio"]

master_doc = "index"
exclude_patterns = ["_build"]

# removes most of the HTML
html_theme = "basic"

drawio_export_directory = os.path.abspath(tempfile.gettempdir() + "/drawio_outdir_test")
