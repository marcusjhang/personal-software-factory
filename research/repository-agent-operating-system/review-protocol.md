# Adversarial research and implementation convergence protocol

## Purpose

Iterate from research and implementation to a decision-grade plan without claiming impossible perfection or absence of unknown risk.

## Review rounds

After the lifecycle and domain-extension research validates, launch independent reviewers for:

1. evidence quality and source/claim integrity;
2. exhaustive lifecycle and state-transition coverage;
3. security, authority, prompt-injection, supply-chain and tenant isolation;
4. human interaction, ideation usability and escalation policy;
5. orchestration, durability, idempotency, leases, cleanup and recovery;
6. self-improvement/evaluation governance and Goodhart resistance;
7. factory DSL, deep-research composition and cross-domain/GTM extensibility;
8. implementation-to-design consistency and runnable test coverage.

Reviewers record findings in a common issue format:

```yaml
id: REVIEW-000
severity: critical | high | medium | low
claim_or_requirement: ""
evidence:
  source_urls: []
  files: []
reproduction: ""
impact: ""
recommended_fix: ""
verification: ""
status: open | confirmed | rejected | fixed | accepted-risk
owner: ""
```

## Triage

A finding changes the plan only after the root agent reproduces it against primary evidence, source, configuration, or an executable test. Duplicate findings are linked. Disagreements are preserved and resolved by version/scope when possible.

- Critical/high: fix before PR or explicitly block the affected capability.
- Medium: fix or record an exact owner, constraint, and future gate.
- Low: fix when cheap or retain as backlog.
- Evidence gap: run focused research rather than inventing a claim.

## Verification after fixes

Run the affected focused tests plus the full suite. Ask a reviewer who did not author the fix to verify closure. A changed architecture or safety boundary triggers another cross-discipline review round.

## Exit criteria

- zero open critical/high findings;
- every medium finding fixed or accepted with owner and gate;
- all declared states have legal entry, exit, cancellation, stale/retry, cleanup and terminal behavior;
- invalid transitions and stale approvals fail closed;
- human-needed decisions are explicit and tested;
- protected policy/evals/permissions cannot be self-approved;
- consumer repositories are isolated and can pin/roll back;
- all research JSON validates and the final report preserves conflicts/uncertainty;
- Python, configuration, SQL and end-to-end tests pass;
- a final independent audit finds no new critical/high issue.

Passing means decision-grade for the declared scope. It is not proof of zero defects or universal production safety.
