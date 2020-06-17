bgzipseek
=========

Python file-like object for read-only seek access of block gzip files. For a description of block gzip see http://www.htslib.org/doc/bgzip.html and https://blastedbio.blogspot.com/2011/11/bgzf-blocked-bigger-better-gzip.html




development
-----------

Install using pip including development extras

```sh
pip install -e .[dev]
```

Enable pre-commit hooks with:

```sh
pre-commit install
```

Note this uses:
 - seed-isort-config to better categorise third party imports
 - isort to sort imports
 - black to format code

Freeze dependencies from `setup.py` to `requirements.txt` with:

```sh
pip-compile
```

Run tests with:

```sh
pytest
```

Test coverage with:

```sh
coverage run --source=bgzipseek -m pytest
coverage report -m
```

Type checking with:

```sh
mypy .
```

See dependencies with:

```sh
pipdeptree
```

Global git ignores per https://help.github.com/en/github/using-git/ignoring-files#configuring-ignored-files-for-all-repositories-on-your-computer

TO run pre-commit hooks without committing:
```sh
pre-commit run --all-files
```
