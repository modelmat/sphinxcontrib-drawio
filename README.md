# sphinxcontrib-drawio
Sphinx Extension to add the ``drawio`` directive to include draw.io diagrams.

**Important:** This extension is in development and not all features will work as advertised or at all.

## Installation

1. ``python3 -m pip install sphinxcontrib-drawio``
2. In your sphinx config:
```python
extensions = [
    "sphinxcontrib.drawio"
]
```
3. Add the binary to $PATH. For Windows add `C:\Program Files\draw.io` and on
Linux add `/opt/draw.io/`. 

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