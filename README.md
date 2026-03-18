# Himalaya Wrapper

A lightweight, zero-dependency Python wrapper for the Himalaya mail client CLI.

## Installation

```bash
pip install -e .
```

## Usage

```python
from himalaya_wrapper import HimalayaClient

client = HimalayaClient(
    unread_cmd="himalaya envelope list --folder INBOX --output json --query unread",
    read_cmd="himalaya message read --folder INBOX {id} --output json",
    mark_read_cmd="himalaya flag add --folder INBOX {id} seen",
)

envelopes = client.list_unread_envelopes()
```

## Publish

```bash
python -m build
python -m twine upload dist/*
```

## TestPyPI Release Candidate Flow

Push a release-candidate tag to trigger the TestPyPI workflow:

```bash
git tag v0.1.0-rc1
git push origin v0.1.0-rc1
```

This runs `.github/workflows/publish-testpypi.yml` and publishes to TestPyPI.
