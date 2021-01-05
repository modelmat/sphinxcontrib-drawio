# sphinxcontrib-drawio

Sphinx Extension adding the `drawio-image` and `drawio-figure` directives.
These are equivalent to the standard `image` and `figure` directives, but
accept the path to a `.drawio` file and additional options to control
exporting of the diagram to a suitable image format. 

These directives replace the `drawio` directive which is now deprecated, and
for which support will be dropped in version 1.0. Deprecation warnings are 
output when a `drawio` directive is encountered. Please replace these with
`drawio-image` orand `drawio-figure`, taking into account these differences:

- the *drawio_output_format* conf.py option has been removed; the draw.io
  diagram is exported to the Sphinx builder's preferred image format (eg. SVG
  for HTML, PDF for LaTeX). The *drawio_builder_export_format* configuration
  variable allows setting another default export format for each builder. Note
  that this can still be overridden for individual `drawio-image` and
  `drawio-figure` directives. See below for details.
- the *scale*, *width* and *height* options have been renamed, respectively, to
  *export-scale*, *export-width* and *export-height* so as not to conflict with
  the options inherited from the [image directive](https://docutils.sourceforge.io/docs/ref/rst/directives.html#image).
- the *export-scale* option now takes an integer percentage; i.e. a value of 100
  means no scaling. This was changed to allow non-integer scaling and offer
  consistency with the `scale` option inherited from the [image directive](https://docutils.sourceforge.io/docs/ref/rst/directives.html#image).
- the *drawio_default_scale* conf.py option has been replaced by the
  *drawio_default_export_scale* option, also accepting a integer percentage
  value.

**Important:** This extension does not work on readthedocs as RTD does not allow
packages (e.g. drawio) to be installed. If you only require diagrams in a single
format, you can consider using editable SVGs or PNGs, accessible through
draw.io's File > Export menu.

The drawio-desktop package does not run without an x-server (e.g. when in a CI
environment), see [this issue](https://github.com/jgraph/drawio-desktop/issues/146).
The workaround is to install `xvfb` and set the `drawio_headless` configuration
option to `auto`.

If any other of the `draw.io` CLI tool's options are wanted, please file an
issue.

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
4. (if running headless), `sudo apt install xvfb`

## Options
These values are placed in the `conf.py` of your sphinx project.

### Binary Path
- *Formal Name*: `drawio_binary_path`
- *Default Value*: `None`

This allows for a specific override for the binary location. By default, this
gets chosen depending on the OS (Linux, Mac, or Windows) to the default
install path of the draw.io program.

### Headless Mode
- *Formal Name*: `drawio_headless`
- *Default Value*: `"auto"`
- *Possible Values*: `True`, `False`, or `"auto"`

This config option controls the behaviour of running the Xvfb server. It is
necessary because `draw.io` will not work without an X-server, see
[this issue](https://github.com/jgraph/drawio-desktop/issues/146).

The `auto` mode will detect whether the program is running in a headless
environment through the `$DISPLAY` environment variable, and act as if it were
set to `True`. If not running on Linux, or the `$DISPLAY` environment variable
contains some value (i.e. running in an X-server on a developer's machine), it
will act as it it were set to `False`.

Setting the value to `True` will start a virtual X framebuffer through the
`Xvfb` command before running any `draw.io` commands, and stop it afterwards.

Setting the value to `False` will run the `draw.io` binary as normal.

### Default Output Format
- *Formal Name*: `drawio_builder_export_format`
- *Default Value*: `{}`

This config option controls the default export file format for each Sphinx
builder. It accepts a dictionary mapping builder names to image formats. The
builder name should match the name of a [Sphinx builder](https://www.sphinx-doc.org/en/master/usage/builders/index.html)
(e.g., `"html"`, `"latex"`). Accepted values for the export format are `"png"`,
`"jpg"`, `"svg"` and `"pdf"`. If no format is set for a given builder, its
preferred image format is used, that is, the first format listed in a builder's
_supported_image_types_ that draw.io is capable of exporting to (eg. SVG for
HTML, PDF for LaTeX). 

### Default Export Scale
- *Formal Name*: `drawio_default_export_scale`
- *Default Value*: `100`
- *Possible Values*: any positive integer

This config option sets the default export scale for all diagrams. This scales
the size of the diagram. So if you take a diagram that by default would output 
a image with a resolution of 50x50 pixels and a scale of 200, you will obtain an
image with a resolution that is approximately 100x100 pixels. By default draw.io
*usually* outputs relatively low resolution images, so this setting can be used
to remedy that. 

This setting will get automatically overridden if the `scale` is set for a
individual diagram in the directive. If either `export-width` or `export-height`
are set for an image, this option will have no effect on the generated image.

### Default Transparency
- *Formal Name*: `drawio_default_transparency`
- *Default Value*:  `False`
- *Possible Values*: `True` or `False`

This changes the background transparency for diagrams exported in *png* format. 
This will be overridden if the transparency is set for a individual diagram in
the directive. If the output format isn't *png*, it will not affect the image
exported.

### No Sandbox
- *Formal Name*: `drawio_no_sandbox`
- *Default Value*: `False`
- *Possible Values*: `True` or `False`

This option may be needed to work in a docker container. You should probably
only enable it if you are experiencing issues. See https://github.com/jgraph/drawio-desktop/issues/144 
for more info. 

## Usage
The extension can be used through the `drawio-image` directive. For example:
```
.. drawio-image:: example.drawio
   :export-scale: 150
```

There's also a `drawio-figure` directive that mimics the `figure` directive:
```
.. drawio-figure:: example.drawio
   :format: png

   An example diagram
```

The directives can be configured with options to control the export of the
draw.io diagram to a bitmap or vector image. These options are documented below.

Additionally, `drawio-image` accepts all of the options supported by the
[image directive](https://docutils.sourceforge.io/docs/ref/rst/directives.html#image).
These options apply to the image as exported by draw.io. Similarly,
`drawio-figure` accepts all options supported by the [figure directive](https://docutils.sourceforge.io/docs/ref/rst/directives.html#figure).

### Format
- *Formal Name*: `:format:`
- *Default Value*: `"png"`
- *Possible Values*: `"png"`, `"jpg"`, `"svg"` or `"pdf"`

This option controls the output file format of *this specific* directive.

### Page Index
- *Formal Name*: `:page-index:`
- *Default Value*: `0`
- *Possible Values*: any integer

This option allows you to select a particular page from a draw.io file to
export. Note that an invalid page-index will revert to one of the other valid
pages (draw.io binary functionality).

### Export Scale
- *Formal Name*: `:export-scale:`
- *Default Value*: `drawio_default_export_scale` set in conf.py
- *Possible Values*: any positive integer

This scales the size of the output image. So if you take a diagram that by
default would output a image with a resolution of 50x50 pixels and a scale of
200, you will obtain an image with a resolution that is approximately 100x100 
pixels. By default draw.io *usually* outputs relatively low-resolution images,
so this setting can be used to remedy that. This overrides the
`drawio_default_export_scale` set in conf.py for this specific diagram. If
either `export-width` or `export-height` are set for a given image,
`export-scale` will have no effect on the generated image.

### Export Width
- *Formal Name*: `:export-width:`
- *Possible Values*: any positive integer

This fits the generated image into the specified width, preserving aspect ratio.
When exporting to a bitmap image, this specifies the width in pixels. For PDF,
a value of 100 corresponds to 1.00 inches.

### Export Height
- *Formal Name*: `:export-height:`
- *Possible Values*: any positive integer

This fits the generated image into the specified height, preserving aspect
ratio. When exporting to a bitmap image, this specifies the height in pixels.
For PDF, a value of 100 corresponds to 1.00 inches.

### Transparency
- *Formal Name*: `:transparency:`
- *Default Value*: `drawio_default_transparency` set in conf.py
- *Possible Values*: `"true"` or `"false"`

This changes the background transparency for diagrams exported to `png` files.
Will override `drawio_default_transparency` which was set in conf.py for this
specific diagram. If this setting is specified while the output format is not
`png` it will have no effect on the generated image
