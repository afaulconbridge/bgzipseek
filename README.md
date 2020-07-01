bgzipseek
=========

[![Build Status](https://travis-ci.com/afaulconbridge/bgzipseek.svg?branch=master)](https://travis-ci.com/afaulconbridge/bgzipseek)
[![PyPI version](https://badge.fury.io/py/bgzipseek.svg)](https://badge.fury.io/py/bgzipseek)

Python file-like object for read-only seek access of block gzip files. For a description of block gzip see http://www.htslib.org/doc/bgzip.html and https://blastedbio.blogspot.com/2011/11/bgzf-blocked-bigger-better-gzip.html


development
-----------

```sh
pip install -e .[dev]  # Install using pip including development extras
pre-commit install  # Enable pre-commit hooks
pre-commit run --all-files  # Run pre-commit hooks without committing
# Note pre-commit is configured to use:
# - seed-isort-config to better categorise third party imports
# - isort to sort imports
# - black to format code
pip-compile  # Freeze dependencies
pytest  # Run tests
coverage run --source=bgzipseek -m pytest && coverage report -m  # Run tests, print coverage
mypy .  # Type checking
pipdeptree  # Print dependencies
```

Global git ignores per https://help.github.com/en/github/using-git/ignoring-files#configuring-ignored-files-for-all-repositories-on-your-computer

For release to PyPI see https://packaging.python.org/tutorials/packaging-projects/
