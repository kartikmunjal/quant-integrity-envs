import os
import subprocess
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "release_review.py"


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Test")
    (repo / "safe.txt").write_text("public material\n", encoding="utf-8")
    git(repo, "add", "safe.txt")
    git(repo, "commit", "-qm", "initial")
    return repo


def run_review(repo: Path, terms: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["RELEASE_REVIEW_TERMS"] = str(terms)
    return subprocess.run(
        [os.sys.executable, str(SCRIPT)], cwd=repo, env=env, text=True, capture_output=True
    )


def test_release_review_passes_clean_repo(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    terms = tmp_path / "terms.txt"
    terms.write_text("private-token\n", encoding="utf-8")
    result = run_review(repo, terms)
    assert result.returncode == 0
    assert result.stdout == "PASS\n"


def test_release_review_reports_location_without_printing_term(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    private_term = "private-token"
    terms = tmp_path / "terms.txt"
    terms.write_text(private_term + "\n", encoding="utf-8")
    (repo / "draft.txt").write_text(f"contains {private_term}\n", encoding="utf-8")
    result = run_review(repo, terms)
    assert result.returncode == 1
    assert result.stdout.startswith("FAIL\n")
    assert "draft.txt:1" in result.stdout
    assert private_term not in result.stdout + result.stderr


def test_release_review_scans_deleted_history(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    private_term = "private-token"
    terms = tmp_path / "terms.txt"
    terms.write_text(private_term + "\n", encoding="utf-8")
    old = repo / "old.txt"
    old.write_text(private_term + "\n", encoding="utf-8")
    git(repo, "add", "old.txt")
    git(repo, "commit", "-qm", "add old")
    old.unlink()
    git(repo, "add", "-u")
    git(repo, "commit", "-qm", "remove old")
    result = run_review(repo, terms)
    assert result.returncode == 1
    assert "history/" in result.stdout and "/old.txt:1" in result.stdout
    assert private_term not in result.stdout + result.stderr
