import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SAMPLES = ROOT / "samples"


@pytest.fixture(scope="session")
def cfg(tmp_path_factory) -> dict:
    """Repo config, with page images written to a temp folder (never into data/)."""
    c = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    c["paths"]["image_dir"] = str(tmp_path_factory.mktemp("images"))
    return c


@pytest.fixture(scope="session")
def small_pdf() -> Path:
    """Smallest sample (28 pages)."""
    return SAMPLES / "Unit 5_Part 2_System Protection.pdf"
