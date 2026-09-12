# Scope decision: plan and research only

**Decision date:** 2026-09-13

The user explicitly changed the deliverable from implementation to a deeply researched, adversarially reviewed implementation plan.

## Final PR includes

- validated research and evidence;
- a complete lifecycle and authority model;
- factory-as-code schema and examples as design specifications;
- ideation, build, maintenance, deep-research and governed-improvement plans;
- human-need decision rules;
- engineering-first, consumer/dogfooding and future GTM roadmap;
- state/transition, security, failure, test, rollout and rollback matrices;
- review findings, fixes and residual uncertainty.

## Final PR excludes

- a claimed working controller or GitHub App;
- deployed PostgreSQL/runtime infrastructure;
- active issue/project mutation workflows;
- production agent-provider integration;
- runnable repository configuration presented as complete implementation.

Exploratory code and SQL produced during planning may be executed to test feasibility or expose contract defects. They are not product deliverables and will be removed before the final commit unless retained as clearly isolated research fixtures with explicit approval.
