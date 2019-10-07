import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sphinxcontrib-drawio",
    version="0.0.1",
    author="Modelmat",
    author_email="modelmat@outlook.com",
    description="Sphinx Extension to include draw.io files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Modelmat/sphinxcontrib-drawio",
    packages=['sphinxcontrib'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.4',
)