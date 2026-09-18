"""GitHub adapter (host assumption: everyone uses GitHub).

Two responsibilities:

- **intake**: read open issues that carry the factory label.
- **handoff**: turn a finished worktree into a **draft pull request**.

Uses the user's authenticated ``gh`` session (a GitHub App is the production
path). All writes are effects: the caller records an intent first and settles a
receipt, so a lost response becomes ``UNKNOWN`` rather than a blind retry.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def available() -> bool:
    return shutil.which("gh") is not None


def _run(args: list[str], cwd: str | Path) -> tuple[int, str, str]:
    p = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def list_issues(repo: str | None = None, label: str = "factory") -> list[dict]:
    """Intake: open issues carrying the factory label."""
    cmd = ["gh", "issue", "list", "--state", "open", "--label", label,
           "--json", "number,title,body,url"]
    if repo:
        cmd += ["--repo", repo]
    rc, out, _ = _run(cmd, cwd=".")
    if rc != 0 or not out:
        return []
    import json
    return json.loads(out)


def publish_draft_pr(workspace: str | Path, *, title: str, body: str,
                     base: str = "main", repo: str | None = None,
                     remote: str = "origin") -> tuple[str | None, str | None]:
    """Commit the worktree, push the branch, open a draft PR.

    Returns ``(pr_url, error)``. This is the only function in PSF that performs
    an external write, and it is only called when the operator opts in.
    """
    ws = str(workspace)
    rc, _, err = _run(["git", "add", "-A"], cwd=ws)
    if rc != 0:
        return None, f"git add failed: {err}"
    # allow an empty-tree guard: only commit if there is something to commit
    rc, _, _ = _run(["git", "diff", "--cached", "--quiet"], cwd=ws)
    if rc != 0:
        rc, _, err = _run(["git", "commit", "-m", title], cwd=ws)
        if rc != 0:
            return None, f"git commit failed: {err}"

    rc, head, err = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ws)
    if rc != 0:
        return None, f"cannot resolve branch: {err}"
    rc, _, err = _run(["git", "push", "-u", remote, head], cwd=ws)
    if rc != 0:
        return None, f"git push failed: {err}"

    cmd = ["gh", "pr", "create", "--draft", "--title", title, "--body", body,
           "--base", base, "--head", head]
    if repo:
        cmd += ["--repo", repo]
    rc, out, err = _run(cmd, cwd=ws)
    if rc != 0:
        return None, f"gh pr create failed: {err}"
    return out.splitlines()[-1] if out else None, None
