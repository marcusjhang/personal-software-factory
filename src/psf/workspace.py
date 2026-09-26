"""Isolated workspaces for agent work.

By default work happens in a throwaway temp directory so the factory can run
without touching the caller's repository. With a git repository and
``use_git=True`` a dedicated ``git worktree`` is created so branches never
collide. Handoff turns the workspace state into a reviewable diff.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

_SKIP_COPY = (".git", ".psf", "node_modules", ".venv", "venv", "__pycache__",
              "dist", "build", ".mypy_cache", ".pytest_cache", ".tox", ".rag")


class Workspace:
    def __init__(self, path: Path, *, is_temp: bool, branch: str | None = None, repo: Path | None = None):
        self.path = path
        self.is_temp = is_temp
        self.branch = branch
        self.repo = repo

    @classmethod
    def create(cls, name: str, *, repo: str | Path | None = None, use_git: bool = False,
               base: str = "HEAD", seed_from: str | Path | None = None) -> "Workspace":
        if use_git and repo is not None:
            repo_path = Path(repo).resolve()
            branch = f"psf/{name}"
            wt_root = repo_path / ".psf" / "worktrees"
            wt_root.mkdir(parents=True, exist_ok=True)
            path = wt_root / name
            if path.exists():
                return cls(path, is_temp=False, branch=branch, repo=repo_path)  # reuse
            # A stale branch from an aborted run would make `worktree add -b` fail.
            listing = subprocess.run(["git", "branch", "--list", branch, "--format", "%(refname)"],
                                     cwd=str(repo_path), capture_output=True, text=True)
            if listing.stdout.strip():
                subprocess.run(["git", "branch", "-D", branch], cwd=str(repo_path),
                               check=False, capture_output=True, text=True)
            subprocess.run(["git", "worktree", "add", "-b", branch, str(path), base],
                           cwd=str(repo_path), check=True, capture_output=True, text=True, timeout=120)
            return cls(path, is_temp=False, branch=branch, repo=repo_path)
        path = Path(tempfile.mkdtemp(prefix=f"psf-{name}-"))
        # A deterministic gate (e.g. `pytest`) needs the project present. With a
        # temp workspace (no --git), seed a copy of the repo so project-file
        # commands have something to run against — this is the no-git quickstart.
        if seed_from is not None:
            src = Path(seed_from).resolve()
            if src.is_dir():
                shutil.copytree(src, path, dirs_exist_ok=True,
                                ignore=shutil.ignore_patterns(*_SKIP_COPY))
        return cls(path, is_temp=True)

    def diff(self) -> str:
        """Return a unified diff of the workspace (git) or a listing (temp)."""
        if self.repo is not None and not self.is_temp:
            r = subprocess.run(["git", "diff", "--no-color", "HEAD"], cwd=str(self.path),
                               capture_output=True, text=True)
            if r.stdout.strip():
                return r.stdout
            r = subprocess.run(["git", "status", "--porcelain"], cwd=str(self.path),
                               capture_output=True, text=True)
            return r.stdout
        files = sorted(p.name for p in self.path.rglob("*") if p.is_file())
        return "\n".join(f"?? {f}" for f in files)

    def cleanup(self) -> None:
        if self.is_temp:
            shutil.rmtree(self.path, ignore_errors=True)
        elif self.repo is not None:
            subprocess.run(["git", "worktree", "remove", "--force", str(self.path)],
                           cwd=str(self.repo), check=False, capture_output=True, text=True)
            if self.branch:
                subprocess.run(["git", "branch", "-D", self.branch], cwd=str(self.repo),
                               check=False, capture_output=True, text=True)

    def __enter__(self) -> "Workspace":
        return self

    def __exit__(self, *exc: object) -> None:
        if self.is_temp:
            self.cleanup()
