from __future__ import annotations

import sys
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("OPENAI_MODEL", "gpt-5-mini")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
