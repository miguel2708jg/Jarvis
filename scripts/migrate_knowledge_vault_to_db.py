"""Import the Obsidian-style knowledge vault into Jarvis database tables.

Usage:
    python scripts/migrate_knowledge_vault_to_db.py --vault Data/knowledge_vault
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.config import settings
from backend.services import knowledge_service


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Jarvis knowledge vault markdown into the database.")
    parser.add_argument("--vault", default=None, help="Knowledge vault path. Defaults to KNOWLEDGE_VAULT_PATH.")
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Do not regenerate the markdown mirror after importing.",
    )
    args = parser.parse_args()

    vault = Path(args.vault or settings.knowledge_vault_path)
    if not vault.exists():
        raise SystemExit(f"Knowledge vault not found: {vault}")

    results = knowledge_service.import_vault_to_db(vault, export_after=not args.no_export)
    for key in ("pages", "sources", "links", "logs"):
        print(f"{key}: {results.get(key, 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
