extensions = ["sphinxcontrib.drawio", "sphinx.ext.imgconverter"]

master_doc = "index"
exclude_patterns = ["_build"]

# removes most of the HTML
html_theme = "basic"

drawio_builder_export_format = {"html": "svg", "latex": "pdf"}
