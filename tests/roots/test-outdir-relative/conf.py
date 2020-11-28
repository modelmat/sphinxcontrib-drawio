extensions = ["sphinxcontrib.drawio"]

master_doc = "index"
exclude_patterns = ["_build"]

# removes most of the HTML
html_theme = "basic"

# this will place the output in the current working directory the test is invoked from
# this directory will be deleted automatically after the test
drawio_export_directory = "_relative_drawio_outdir_test"
