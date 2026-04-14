# agon

> Assess a source archive inside an ephemeral Ubuntu LXD container and compute a weighted total grade.

## Table of Contents

- [About](#about)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Development](#development)
- [License](#license)

## About

**agon** launches a fresh Ubuntu LXD container, uploads an archive, extracts it, runs quality checks in isolation, shows colored weighted grades, reports a total grade, opens an interactive shell, and deletes the container unless told to keep it.

## Requirements

- Python 3.9 or later
- LXD installed and initialized (`lxc` command available)

## Installation

Ideally, run your test inside a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install directly from the repository root:

```bash
pip install .
```

## Usage

```bash
agon [--version] [--help] [--image IMAGE] [--container-archive-upload-path PATH] [--container-extract-path PATH] [--keep-container] ARCHIVE
```

### Arguments

| Argument | Description |
|---------|-------------|
| `ARCHIVE` | Path to a `.zip` or tar archive containing the code to check. |

### Options

| Option | Description |
|--------|-------------|
| `--image` | LXD image alias to launch. Default: `ubuntu:24.04` |
| `--container-archive-upload-path` | Upload directory in the container. Default: `/home/ubuntu/` |
| `--container-extract-path` | Extraction directory in the container. Default: `/home/ubuntu/extracted/` |
| `--keep-container` | Keep the container after checks instead of deleting it. |

### Examples

```bash
# Show help
agon --help

# Show version
agon --version

# Run checks on an archive in a fresh Ubuntu LTS container
agon ./my-project.tar.gz

# Keep the container for manual inspection after checks
agon ./my-project.zip --keep-container
```

## Workflow

1. Launches a new Ubuntu LTS LXD container.
2. Waits for the container to become ready and refreshes apt metadata.
3. Uploads the archive into the container.
4. Extracts the project inside the container.
5. Shows the extracted tree with `tree -hClsa`.
6. Installs required Debian packages for assessments as needed.
7. Runs archive-format, pylint, and flake8 assessments.
8. Prints colored weighted results and a total grade.
9. Opens an interactive shell as `ubuntu`.
10. Deletes the container unless `--keep-container` is used.

## Development

Clone the repository and install in editable mode:

```bash
git clone https://github.com/ahresse/agon.git
cd agon
pip install -e .
```

Run the test suite:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

## License

Distributed under the terms of the [MIT License](LICENSE).
