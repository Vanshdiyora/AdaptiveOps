from pathlib import Path

import pytest

from app.services.repository.local import LocalRepositoryProvider


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "src").mkdir()
    (root / "src" / "service.py").write_text(
        "def process_payment():\n    raise PaymentTimeoutException()\n",
        encoding="utf-8",
    )
    (root / "src" / "helpers.py").write_text(
        "def helper():\n    return 'ok'\n",
        encoding="utf-8",
    )
    (root / "node_modules").mkdir()
    (root / "node_modules" / "bad.js").write_text("console.log('ignored')\n")
    (root / "binary.dat").write_bytes(b"\x00\x01\x02\x03")
    return root


def test_valid_repository_path(repo_root: Path):
    provider = LocalRepositoryProvider(repo_root)
    assert provider.root == repo_root.resolve()
    assert provider.is_valid


def test_missing_path_raises():
    with pytest.raises(ValueError, match="Repository path"):
        LocalRepositoryProvider(Path("/definitely/missing/path"))


def test_path_traversal_is_blocked(repo_root: Path):
    provider = LocalRepositoryProvider(repo_root)
    with pytest.raises(ValueError, match="outside the repository root"):
        provider.read_file("../outside.txt")


def test_ignored_directories_are_excluded(repo_root: Path):
    provider = LocalRepositoryProvider(repo_root)
    files = provider.list_files()
    assert "node_modules/bad.js" not in files
    assert "src/service.py" in files


def test_search_and_file_read(repo_root: Path):
    provider = LocalRepositoryProvider(repo_root)
    results = provider.search("PaymentTimeoutException")
    assert results
    assert results[0]["file"] == "src/service.py"
    read_back = provider.read_file("src/service.py", 1, 10)
    assert read_back["snippet"]
    assert "PaymentTimeoutException" in read_back["snippet"]


def test_tree_generation(repo_root: Path):
    provider = LocalRepositoryProvider(repo_root)
    tree = provider.get_tree(max_depth=2, max_files=20)
    assert "src" in tree
    assert "service.py" in tree
