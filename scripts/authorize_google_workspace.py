"""Run a one-off Google Workspace OAuth authorization flow."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    os.environ["GOOGLE_ALLOW_INTERACTIVE_OAUTH"] = "true"

    from backend.services.google_workspace_client import get_credentials, token_file

    get_credentials()
    print(f"OAuth OK: {token_file() or 'token.json'} created")


if __name__ == "__main__":
    main()
