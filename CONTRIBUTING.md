# Contributing to sphinxcontrib-drawio

If you have an bug or issue, please [file an issue](https://github.com/Modelmat/sphinxcontrib-drawio/issues) using the relevant template.

## Adding new functionality
* Please ensure that all relevant changes are documented in the README
* Ensure that your code meets the black formatter standards (run the formatter)

## Releasing new versions
To release a new version, create a new commit which increases `__version__`
inside `sphinxcontrib/drawio/__init__.py`. Then use GitHub relases to
"Draft a new release" by creating a new tag named with the version.
This will trigger the CI to push to pypi.
