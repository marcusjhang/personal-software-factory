# Database reference (PostgreSQL 16+)

This database is the runtime system of record for events, approvals, attempts, leases, idempotency, and effects. Git is the desired configuration and reviewed-spec source of truth. GitHub owns its issue/project resources, but those resources are only a reconciled, human-facing projection. A GitHub label never grants authority.

## Local use

```sh
cd deploy
docker compose up -d
export DATABASE_URL=postgresql://polar_admin:polar_local_only@localhost:5432/polar
../tests-sql/run.sh
```

The image applies `migrations/*.sql` in lexical order only when it initializes a new volume. To reset disposable local data, run `docker compose down -v` and start it again. For an existing database, use a real migration runner or apply a new, reviewed migration exactly once. `deploy/migrate.sh` is a small reference helper, not a production migration ledger or lock manager.

Do not use the checked-in local password outside a developer machine. Production must use managed secrets, TLS, backups, point-in-time recovery, restricted administrator access, and a migration lock/ledger.

## Roles and trust boundary

| Role | Purpose |
|---|---|
| `polar_owner` | `NOLOGIN` schema owner used by migrations |
| `polar_runtime` | trusted control-plane service group; runtime writes |
| `polar_reconciler` | GitHub observation and effect reconciliation group |
| `polar_auditor` | read-only group |
| `polar_agent` | `NOLOGIN` marker with **no privileges** |

Create separate `LOGIN` roles for deployed services and grant only the matching group role. Never grant a group role to an agent sandbox. Agents submit proposals through an authenticated service boundary. They cannot approve, promote, lease, or authorize themselves. Database administrators can bypass controls, so admin access and exported audit anchoring need separate operational controls.

The reference schema is one trust domain and does not enable row-level security. Add reviewed RLS policies before storing mutually untrusted tenants in one database.

## Main records

- `webhook_inbox` and `idempotency_keys`: durable ingress, delivery deduplication, and request idempotency.
- `work_items`, `spec_revisions`, `readiness_decisions`, and `approvals`: lifecycle state and exact-hash authorization evidence.
- `event_ledger` and `audit_log`: append-only domain/security history.
- `leases` and `attempts`: one unreleased lease and monotonically increasing fencing tokens.
- `evidence_bundles`: immutable content-addressed verification evidence.
- `outbox_effects`, `effect_attempts`, and `effect_receipts`: at-least-once remote effects and receipts.
- `github_projection_observations` and `github_projection_drift`: immutable observations and classified reconciliation work.
- `deployments`, `outcomes`, and `eval_candidates`: rollout, observation, and governed self-improvement.

Lifecycle values are `INBOX`, `TRIAGED`, `PLANNING`, `NEEDS_CLARIFICATION`, `READY_REVIEW`, `READY`, `LEASED`, `IMPLEMENTING`, `VERIFYING`, `REVIEW`, `MERGE_QUEUED`, `MERGED`, `DEPLOYING`, `OBSERVING`, `DONE`, plus `BLOCKED`, `CANCELLED`, and `ROLLED_BACK`.

## Required application transactions

SQL supplies useful guardrails, but it does not prove all control-plane invariants.

### Readiness

1. Load the immutable current spec revision and deterministic Definition-of-Ready policy.
2. Canonicalize inputs and compute SHA-256 outside PostgreSQL.
3. Evaluate every DoR rule deterministically.
4. For `READY`, lock the work item and load an `APPROVED` `READINESS` approval whose `subject_sha256` exactly equals `inputs_sha256`.
5. Reject an expired or invalidated approval. Verify the approver is authorized and is not the proposing agent.
6. Insert `readiness_decisions`, append event/audit rows, and update the cached work-item state in one transaction.

The composite foreign key prevents a readiness row from referencing an approval for another item or hash. It does not check current time, approval kind, canonical JSON, approver policy, or whether all material inputs were included. Any material input change must invalidate the approval and recompute readiness. Treat `work_items.lifecycle_state = 'READY'` and GitHub labels as projections, never standalone authorization.

### Leasing and fencing

Acquire with a work-item lock. Close any expired unreleased lease, allocate the new database sequence token, insert the lease, then append audit/event rows. The partial unique index allows only one **unreleased** lease. Time passing does not alter an index predicate, so an expired lease must be closed transactionally before replacement.

Every mutating operation must carry `(lease_id, work_item_id, fencing_token)` and compare it with the current unreleased, unexpired lease in the same transaction. The attempt foreign key proves the token belonged to that lease; it cannot by itself reject a formerly valid token after lease release.

### Inbox, idempotency, and effects

Insert webhook delivery and acknowledge it only after commit. Duplicate `(provider, delivery_id)` is success. On idempotency-key reuse, compare `request_sha256`; never return a response for different request bytes.

Write business changes and `outbox_effects` in one transaction. Dispatch with short row claims (for example, `FOR UPDATE SKIP LOCKED`), a stable `idempotency_key`, bounded retry/backoff, and durable `effect_attempts`. A timeout after sending is `UNKNOWN`, not `FAILED`. Observe the remote resource and reconcile before retrying. Remote receivers must deduplicate because delivery is at least once. Store confirmed remote evidence in immutable receipts.

### GitHub reconciliation

Persist the remote observation first. Compare its hash/version with Git desired state and classify drift. `UNKNOWN` and `CONFLICT` require another observation or human decision; do not overwrite blindly. GitHub issue state, labels, and project fields can aid humans but cannot create readiness, approval, a lease, merge authority, or promotion authority.

### Approval invalidation and deployment

Approvals bind to exact canonical digests and have explicit expiry/invalidation. The trusted service must verify the correct approval kind and digest at the point of use. Deployments and promotions must recheck approval and evidence under a lock rather than relying on a prior UI state.

### Self-improvement

Allowed progression is proposal -> curated eval -> offline -> shadow -> canary -> promoted. Agents can create proposals only through the service. Trusted code must enforce ordered transitions, risk budgets, evaluation thresholds, rollback conditions, and a human promotion approval bound to the exact candidate digest. Table checks only ensure required hashes/references exist at later stages.

## Immutability and audit limits

Triggers reject update/delete on spec revisions, event ledger, evidence bundles, effect receipts, GitHub observations, outcomes, and audit rows. Corrections are new rows. These controls deter normal service roles, not owners or superusers. Use restricted admin access, WAL/backups, external log export, and periodic digest anchoring when tamper evidence matters.
