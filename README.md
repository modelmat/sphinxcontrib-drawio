# sphinxcontrib-drawio
Sphinx Extension to add the ``drawio`` directive to include draw.io diagrams.

**Important:** This extension is in development and not all features will work as advertised or at all.

The drawio-desktop package does not run without an x-server (e.g. when in a CI
environment), see
[this issue](https://github.com/jgraph/drawio-desktop/issues/146).
The workaround is to install `xvfb-run` and set the `drawio_headless` config to `True`.

## Installation

1. `python3 -m pip install sphinxcontrib-drawio`
2. In your sphinx config:
```python
extensions = [
    "sphinxcontrib.drawio"
]
```
3. Add the binary to `$PATH`. For Windows add `C:\Program Files\draw.io` and on
Linux add `/opt/draw.io/`. 
4. (required by default, see below) `sudo apt install xvfb`

## Options
These are the available options and their default values.

```python
drawio_output_format = "png" # from ["png", "jpg", "svg"]
drawio_binary_path = "/path/to/draw.io-binary"
drawio_headless = False
```

## Usage
```
.. drawio:: example.drawio
    :format: png
    :alt: An Example
    :align: center
```
If any other of the `draw.io` CLI tool's options are wanted, please file an issue.