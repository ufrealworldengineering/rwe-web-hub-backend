from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from db.models import Base  # noqa: E402
from db.session import engine  # noqa: E402


def main() -> int:
    load_dotenv()

    # Guardrail: never run destructive operations against production.
    env_name = os.getenv("ENV", "local").lower()
    if env_name in {"prod", "production"}:
        raise RuntimeError("Refusing to clear DB with ENV=production.")

    # Requires DATABASE_URL to be set (db.session reads it).
    Base.metadata.drop_all(bind=engine)
    print("Dropped all tables.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

