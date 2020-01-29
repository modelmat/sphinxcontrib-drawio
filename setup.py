import subprocess

import setuptools

# This will fail if something happens or if not in a git repository.
# This is intentional.
ret = subprocess.run("git describe --tags --abbrev=0", stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE, check=True, shell=True)
version = ret.stdout.decode("utf-8").strip()

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sphinxcontrib-drawio",
    version=version,
    author="Modelmat",
    author_email="modelmat@outlook.com.au",
    description="Sphinx Extension to include draw.io files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Modelmat/sphinxcontrib-drawio",
    packages=['sphinxcontrib'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: Sphinx :: Extension",
    ],
    python_requires='>=3.6',
)
