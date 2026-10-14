import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SAMPLES = ROOT / "samples"


@pytest.fixture(scope="session")
def cfg() -> dict:
    return yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def small_pdf() -> Path:
    """Smallest sample (28 pages)."""
    return SAMPLES / "Unit 5_Part 2_System Protection.pdf"
