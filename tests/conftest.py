import shutil
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def make_registry(tmp_path):
    """Build a registry from the base fixture with a named fixture's files laid over it."""

    def build(name: str | None = None) -> Path:
        root = tmp_path / "subset"
        shutil.copytree(FIXTURES / "base", root)
        if name is not None:
            shutil.copytree(FIXTURES / name, root, dirs_exist_ok=True)
        return root

    return build
