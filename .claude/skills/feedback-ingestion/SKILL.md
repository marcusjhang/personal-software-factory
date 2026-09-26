---
name: feedback-ingestion
description: >
  Ingest consumer feedback issues into the factory and act on them safely:
  pull the issues, extract each concrete claim, verify it against HEAD before
  believing it, fix the valid ones with a regression test, close the issue with
  evidence, then run an OCR high-severity loop (fix highs, repeat) until no
  verified highs remain. Use when a maintainer says "there's feedback in the
  issues", "check the issues and improve the factory", "triage the feedback
  issues", or after ingesting `factory-feedback` envelopes.
license: MIT
compatibility: >
  Requires `gh` (issues) and, for the review phase, the `ocr` CLI
  (`npm install -g @alibaba-group/open-code-review`). Runs in the factory repo.
---

# Feedback ingestion

Consumer repos file feedback as GitHub issues (labelled `factory-feedback`) and
as metric envelopes. This skill turns that raw signal into verified fixes — never
trusting a report at face value.

## Principle: verify before you believe

A feedback issue is a *claim*, not a bug. Reproduce it against the current `HEAD`
first. Many reports are already fixed, environment-specific, or wrong. Only a
reproduced (or code-evident) claim is "valid". Fix valid claims; cite evidence and
close. Never "fix" a phantom.

## Step 1 — Gather

```bash
gh auth switch --user <you>            # gh account flips; make sure it's right
gh issue list -R <owner>/<repo> --state all --limit 100
psf feedback ingest --issues --github <owner>/<repo>   # envelopes -> .psf/feedback/inbox
psf feedback report                                     # aggregate signals
```

Read every non-envelope issue in full: `gh issue view <n> -R <owner>/<repo> --json title,body`.
Envelope issues (title `[factory-feedback] FB-…`) carry counts/digests only — ingest
them for signal, then close them as consumed.

## Step 2 — Extract claims and verify each

For every issue, list the concrete, falsifiable claims (a file, a command, an
observed output). For each claim, on current `HEAD`:

1. Read the cited code (`file:line`).
2. Reproduce with the smallest probe (a script, a test, a CLI run).
3. Classify: **valid** (reproduces), **already-fixed** (cite the commit/test),
   **invalid** (contradicted), **unreproducible** (needs an env you lack — say so).

Record the classification per claim; do not start editing yet.

## Step 3 — Fix the valid ones

- Smallest correct change; prefer the fix that makes the user's documented path work.
- Prove it: add a failing-then-passing regression test (a new eval id — `X*` e2e,
  `H*` guardrail, `A*` adapter — matching where the bug lives).
- If a signal suggests a config change (e.g. "raise `max_attempts`"), run
  `psf improve` and let the protected eval decide; don't hand-tune.
- Run the battery (Step 5) before closing anything.

## Step 4 — Close with evidence

For each issue, comment with: the classification, the repro, the fix, the file,
and the commit SHA; then close. For already-fixed ones, cite the commit and test.
For invalid/unreproducible, say why and close (or leave open only if truly blocked).

## Step 5 — OCR high-severity loop

```bash
ocr delegate preview --format json                       # which files/mode
ocr delegate rule --format json <changed files>          # review rules
git diff / git show <commit> -- <file>                   # the code to review
```

Review every changed file against the rules; gather findings with a severity.
Then, from the current tree:

1. Fix every **critical/high** finding; add a test where it is a behavioral bug.
2. Re-run the battery (Step 6).
3. Re-run OCR on the files you just changed.
4. **Repeat until a pass yields no verified high-or-above finding.** Write the
   rounds into `docs/EVAL-FINDINGS.md`.

Never declare "no highs" without the OCR pass that produced it.

## Step 6 — Battery (must be green)

```bash
PYTHONPATH=src python3 -m pytest -q
for s in eval-self eval-gov eval-supervisor eval-adapters eval-guardrails eval-e2e; do
  PYTHONPATH=src python3 -m psf.cli $s; done
PYTHONPATH=src python3 -m psf.cli eval-repos
PYTHONPATH=src python3 -m psf.cli eval-oss       # live harness
PYTHONPATH=src python3 -m psf.cli bench
PYTHONPATH=src python3 -m psf.cli audit         # must be healthy: True
```

## Step 7 — Land it

```bash
gh auth switch --user <you>
git push origin <branch>:main
```

Report per issue: valid/invalid, fix + test id, commit SHA, and the final battery.
