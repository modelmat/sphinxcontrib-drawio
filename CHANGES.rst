sphinxcontrib-drawio Release History
------------------------------------

Release 0.0.13
~~~~~~~~~~~~~~

- Support for the ``drawio_builder_export_format`` configuration variable was
  dropped. The extension now automatically exports the draw.io diagram to a
  format preferred by the active Sphinx builder (e.g. SVG for HTML, PDF for
  LaTeX).
- The extension now works by registering an ImageConverter post-tranform which
  aligns well with the provided functionality and helps solve a number of
  issues (#52, #55).
