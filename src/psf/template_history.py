"""Frozen copies of past factory templates (never edit a shipped entry).

Repos scaffolded before ``psf.lock.json`` existed have no recorded merge base.
They came from template 0.1.0 or earlier, so that is the honest base for a three-way
upgrade: anything added upstream since (new files, new lines) then arrives as an
addition instead of being mistaken for a local deletion.
"""

from __future__ import annotations

FACTORY_YML_0_1_0 = 'schemaVersion: psf/v1\nname: default\ndescription: Default personal software factory.\nrunner: mock\nmode: "{mode}"          # hitl = human in the loop; yolo = human out (autonomous)\nagents:\n  triage:    { prompt: agents/triage.md }\n  spec:      { prompt: agents/spec.md }\n  implement: { prompt: agents/implement.md }\n  verify:    { prompt: agents/verify.md }\n  review:    { prompt: agents/review.md }\ngates:\n  spec_approval: true\n  verify_quorum: 2\nlimits:\n  max_attempts: 2\nfeedback:\n  upstream: {upstream}\n  mode: "{fb_mode}"          # off | hint | auto; change anytime with `psf feedback opt-out|opt-in`\nclassifier:\n  provider: "mock"          # mock | jev (TypeSafe). Advisory only.\n  supervisor:\n    enabled: false           # opt-in: watch a worker and steer/stop/retry\n    thresholds: {needs_human: 0.80, off_track: 0.80, stuck: 0.80, progress: 0.40}\n    max_steers: 1\n    max_retries: 1\n'

AGENTS_MD_0_1_0 = '# AGENTS.md — how agents should use this repository\n\nThis repository is driven by a **personal software factory** (`psf`). If you are\nan agent working here, follow this process instead of ad-hoc editing — route\nchanges through the factory so they get a spec, approval, independent\nverification, and review:\n\n1. `psf validate` — confirm the factory definition compiles.\n2. `psf run "<goal>"` — run the goal through the factory (intake -> spec ->\n   approval -> build -> **independent verify** -> review -> handoff).\n3. `psf status` / `psf audit` — check state and health before you finish.\n4. Record the real outcome: `psf outcome <work-id> --accepted [--cost N --minutes N]`.\n\n## Feedback to the factory\n\nAt the end of a work cycle, send a **privacy-filtered** usage envelope back to the\nfactory that powers this repo. It contains **counts, digests, and versions only** —\nnever source code, prompts, file paths, or secrets:\n\n    psf feedback export --github <upstream-repo>\n\n`<upstream-repo>` is the `feedback.upstream` value in `factory/factory.yml`.\nSet `feedback.mode: auto` to make `psf feedback export` publish there by default.\nRecurring verify-failures and blocks become evaluation cases and improvements in\nthe upstream factory. This is evidence, never authority: it cannot change policy.\n\nDo **not** put secrets, customer data, or raw source in a feedback envelope.\n'

PROMPTS_0_1_0 = {'triage': 'You scope a goal: restate it, classify risk, and decide spec-first vs direct. Reply reject only for a non-goal.', 'spec': "You write a typed spec: title, desired behavior, non-goals, and acceptance criteria that a verifier can check.\n\nAcceptance criteria must be behavioral and testable:\n- Each criterion states an observable outcome: given input X, the system does Y (succeeds, rejects, returns, persists, a test passes). A verifier must be able to run it.\n- Do not quote exact error, log, or message wording.\n- Do not require internal fields, names, or structure the goal did not ask for.\n- Do not require particular test cases, test names, or coverage counts. Ask that the project's tests pass; do not dictate which cases they contain.\n- If a criterion cannot be stated behaviorally, drop it or record it as a non-goal.", 'implement': 'You make the smallest change that satisfies the spec in the given workspace. Report an artifact digest.', 'verify': 'You independently reproduce and check the change against the frozen spec. You are not the implementer. Return pass/fail and findings.\n\nFail only on behavioral or acceptance failures: an acceptance criterion is not met, a test fails, the change does not do what the spec says, or it breaks existing behavior.\n\nCosmetic wording and incidental internal differences are advisory, never failures: exact error/log/message text, naming, formatting, file layout, and internal fields the spec did not require. Report them as findings prefixed "advisory:" and still pass.\n\nTest-coverage completeness (which specific cases exist) is advisory unless the goal explicitly required those cases. If the tests pass and the behavior is correct, pass.', 'review': "You assess quality, risk, and fit against the spec. Approve or request changes.\n\nApprove when the acceptance criteria are met and the project's tests pass. Do not request changes for style, naming, test-coverage preferences, or hypothetical improvements.\n\nIf you request changes, you MUST give concrete notes naming the defect and the fix. Never revise without actionable notes; if you cannot name a real defect, approve."}


def render_0_1_0(upstream: str, fb_mode: str, mode: str) -> dict[str, str]:
    """The 0.1.0 template, rendered exactly as `psf init` 0.1.0 wrote it."""
    files = {
        "factory.yml": FACTORY_YML_0_1_0.replace("{upstream}", upstream)
                                        .replace("{fb_mode}", fb_mode)
                                        .replace("{mode}", mode),
        "AGENTS.md": AGENTS_MD_0_1_0,
    }
    for role, prompt in PROMPTS_0_1_0.items():
        files[f"agents/{role}.md"] = prompt + "\n"
    return files
