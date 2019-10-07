# sphinxcontrib-drawio
Sphinx Extension to add the ``drawio`` directive to include draw.io diagrams.

**Important:** This extension is in development and not all features will work as advertised or at all.

## Installation

``python3 -m pip install sphinxcontrib-drawio``

## Options
```
drawio_default_image_format = "png"
```

## Usage
```
.. drawio:: example.drawio
    :format: png
    :alt: An Example
    :align: center
```
If any other of the `draw.io` CLI tool's options are wanted, please file an issue.