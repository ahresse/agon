#!/usr/bin/env python3
"""
generate_test_project.py

Generate a minimal Python project tar.gz with a README whose quality varies
according to the requested level.  Intended for use as test input for agon.

Usage:
    python generate_test_project.py very-bad  # outputs very-bad-project.tar.gz
    python generate_test_project.py bad
    python generate_test_project.py good
    python generate_test_project.py very-good
"""

import argparse
import io
import os
import sys
import tarfile


QUALITY_LEVELS = {"very-bad", "bad", "good", "very-good"}


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate a minimal Python project archive for agon testing."
    )
    parser.add_argument(
        "quality",
        choices=sorted(QUALITY_LEVELS),
        help="Desired README / project quality level.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output tar.gz path (default: <quality>-project.tar.gz).",
    )
    return parser.parse_args(argv)


def _readme(quality: str) -> str:
    """Return a README.md string tuned to the requested quality."""

    if quality == "very-bad":
        return """\
# myproj

TODO write readme
"""

    if quality == "bad":
        return """\
myproj
======

this is a python project.

install
-------

run `pip install .`

usage
-----

import myproj and use it.
"""

    if quality == "good":
        return """\
# myproj

A small utility module.

## Installation

```bash
pip install .
```

## Usage

```python
from myproj.core import hello
hello("world")
```

## License

MIT
"""

    # very-good
    return """\
# myproj

[![CI](https://github.com/example/myproj/actions/workflows/ci.yml/badge.svg)](https://github.com/example/myproj/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> A small, well-documented utility module for greeting users.

## Table of Contents

- [About](#about)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## About

`myproj` provides a simple, reusable `hello` function that prints a personalised greeting.

## Requirements

- Python 3.9 or later

## Installation

Ideally, run inside a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install directly from the repository root:

```bash
pip install .
```

## Usage

```python
from myproj.core import hello

hello("world")   # prints: Hello, world!
```

## Development

Clone the repository and install in editable mode:

```bash
git clone https://github.com/example/myproj.git
cd myproj
pip install -e ".[dev]"
```

Run the test suite:

```bash
python -m pytest tests/ -v
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

Distributed under the terms of the [MIT License](LICENSE).
"""


def _python_code(quality: str) -> str:
    """Return the main Python module tuned to the requested quality."""

    if quality == "very-bad":
        return """\
x=1
def f():
 print("hi")
"""

    if quality == "bad":
        return """\
def hello(name):
    print("Hello, " + name + "!")

if __name__ == "__main__":
    hello("world")
"""

    if quality == "good":
        return '''\
def hello(name: str) -> None:
    """Print a greeting."""
    print(f"Hello, {name}!")


if __name__ == "__main__":
    hello("world")
'''

    # very-good
    return '''\
"""Greeting utilities."""

from __future__ import annotations


def hello(name: str, greeting: str = "Hello") -> None:
    """Print a personalised greeting to stdout.

    Args:
        name: The name of the person to greet.
        greeting: The greeting word to use. Defaults to "Hello".

    Raises:
        ValueError: If *name* is empty or contains only whitespace.

    Examples:
        >>> hello("world")
        Hello, world!
    """
    if not name or not name.strip():
        raise ValueError("name must be a non-empty string")
    print(f"{greeting}, {name}!")


if __name__ == "__main__":
    hello("world")
'''


def _license(quality: str) -> str:
    """Return a LICENSE file tuned to the requested quality."""

    if quality in ("very-bad", "bad"):
        return ""

    if quality == "good":
        return """\
MIT License

Copyright (c) 2024 Example Author

Permission is hereby granted...
"""

    # very-good
    return """\
MIT License

Copyright (c) 2024 Example Author

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def _requirements(quality: str) -> str:
    """Return a requirements.txt tuned to the requested quality."""

    if quality in ("very-bad", "bad"):
        return ""

    if quality == "good":
        return "requests\n"

    return """\
requests>=2.31.0
pydantic>=2.0.0
"""


def _pyproject(quality: str) -> str:
    """Return a pyproject.toml tuned to the requested quality."""

    if quality in ("very-bad", "bad"):
        return ""

    if quality == "good":
        return """\
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "myproj"
version = "0.1.0"
description = "A small utility module."
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.9"
"""

    return """\
[build-system]
requires = ["setuptools>=61", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "myproj"
version = "0.1.0"
description = "A small, well-documented utility module for greeting users."
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.9"
authors = [
    {name = "Example Author", email = "author@example.com"},
]
keywords = ["greeting", "utility", "cli"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "requests>=2.31.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]

[project.scripts]
myproj = "myproj.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.black]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I"]

[tool.mypy]
python_version = "3.9"
strict = true
"""


def _test_module(quality: str) -> str:
    """Return a test file tuned to the requested quality."""

    if quality in ("very-bad", "bad", "good"):
        return ""

    return '''\
"""Tests for myproj.core."""

import pytest

from myproj.core import hello


def test_hello_basic(capsys):
    hello("world")
    captured = capsys.readouterr()
    assert captured.out == "Hello, world!\\n"


def test_hello_custom_greeting(capsys):
    hello("world", greeting="Hi")
    captured = capsys.readouterr()
    assert captured.out == "Hi, world!\\n"


def test_hello_empty_name():
    with pytest.raises(ValueError):
        hello("")
'''


def _directory_layout(quality: str) -> dict[str, str]:
    """Return a dict mapping relative file paths to content strings."""
    files: dict[str, str] = {}

    # Core module
    files["myproj/core.py"] = _python_code(quality)
    files["myproj/__init__.py"] = ""

    # README
    files["README.md"] = _readme(quality)

    # LICENSE (only good / very-good)
    license_text = _license(quality)
    if license_text.strip():
        files["LICENSE"] = license_text

    # requirements.txt (only good / very-good)
    reqs = _requirements(quality)
    if reqs.strip():
        files["requirements.txt"] = reqs

    # pyproject.toml (only good / very-good)
    pyproj = _pyproject(quality)
    if pyproj.strip():
        files["pyproject.toml"] = pyproj

    # tests (only very-good)
    tests = _test_module(quality)
    if tests.strip():
        files["tests/test_core.py"] = tests
        files["tests/__init__.py"] = ""

    return files


def _create_tarball(path: str, files: dict[str, str]) -> None:
    """Write a gzipped tar archive containing *files* to *path*."""
    root_dir = os.path.splitext(os.path.splitext(os.path.basename(path))[0])[0]

    with tarfile.open(path, "w:gz") as tar:
        for rel_path, content in files.items():
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name=f"{root_dir}/{rel_path}")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))


def main(argv=None) -> int:
    args = _parse_args(argv)
    output_path = args.output or f"{args.quality}-project.tar.gz"

    files = _directory_layout(args.quality)
    _create_tarball(output_path, files)

    print(f"Generated {output_path} ({len(files)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
