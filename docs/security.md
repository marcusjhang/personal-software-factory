# Security Model

**Status:** Proposed controls and verification requirements. No statement here asserts that these controls are implemented or production-tested.

## 1. Security objectives

The design must:

- prevent issue text, code, logs, models, or agents from granting authority;
- preserve separation between proposal, approval, execution, verification, merge, deployment, and promotion;
- limit a compromised worker to one attempt's approved scope and time;
- reject stale workers and replayed/duplicated effects;
- bind approvals, checks, artifacts, and releases to exact content;
- keep credentials and sensitive evidence out of prompts, repositories, logs, and public issues;
- fail closed on ambiguous identity, permission, effect outcome, or destructive drift;
- retain sufficient tamper-evident evidence for investigation and recovery.

## 2. Threat model

### Assets

Protected Git policy/specs/evals, PostgreSQL events and approvals, signing keys, GitHub App keys and installation tokens, webhook secrets, source and artifacts, branch/ruleset/CODEOWNERS settings, Project schema, production credentials, telemetry, evaluation datasets, and human identities.

### Adversaries and failures

- a malicious issue author, pull request, dependency, repository file, log line, web page, or MCP/tool response;
- a compromised or hallucinating agent, model provider, action, runner, dependency, or controller component;
- an authorized human making an error or attempting a bypass;
- a stale worker after lease expiry, duplicated delivery, lost acknowledgment, partial API mutation, or split brain;
- a malicious insider with one but not all required roles;
- supply-chain compromise, cache poisoning, credential disclosure, artifact substitution, and rollback tampering.

GitHub warns that attacker-controlled contexts must not be interpolated directly into shell and recommends least-privilege tokens, full-SHA action pinning, and CODEOWNER protection for workflows ([secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)). OWASP identifies prompt injection and excessive agency as distinct LLM application risks; prompts alone are not an authorization mechanism ([prompt injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/), [excessive agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/)).

## 3. Identity and authorization

### Human identities

Use organization-managed GitHub identities with strong authentication. Authorization maps a verified principal to versioned roles such as product owner, technical owner, CODEOWNER, security owner, deploy approver, incident commander, eval curator, and promoter. Store the role snapshot and source review ID with each approval. Role removal invalidates unconsumed approval where policy requires.

### Service identities

Separate at least these logical identities:

1. **Webhook/read observer:** read-only GitHub access.
2. **Controller/reconciler:** managed issue/Project writes; no code approval or merge.
3. **Implementation worker:** short-lived branch-scoped write after lease; no approval, merge, deploy, ruleset, Project schema, or secret administration.
4. **Verifier:** read-only code and artifact upload/check reporting; no production secret or repository write.
5. **Merger:** queue/merge only after controller predicate and ruleset enforcement.
6. **Deployer:** one environment/artifact scope; cannot author or approve.
7. **Promotion controller:** can activate only a human-approved exact policy/artifact digest.

Prefer GitHub App installation tokens with minimum repository selection and permissions. Tokens are short-lived and minted only after policy admission. GitHub documents App tokens as the route when `GITHUB_TOKEN` lacks required permission and recommends minimizing `permissions` ([automatic token authentication](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)); organization Projects require separate App access ([Actions and Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions)).

### Non-delegable rules

Agents may not:

- approve their own spec, patch, exception, deploy, evaluation, or promotion;
- alter App installations, permissions, secrets, rulesets, CODEOWNERS, approval quorum, risk policy, evaluator, or promotion threshold through runtime tool use;
- convert issue instructions, a label, model consensus, a passing self-written test, or Project status into authorization;
- mint/extend a lease or capability;
- make an unknown external effect safe merely by retrying it.

## 4. GitHub Actions controls

- Default `permissions: {}` and grant per-job minimum permissions.
- Pin every third-party action to a reviewed full commit SHA. Allow only approved actions/owners.
- Protect `.github/workflows/**`, action code, dependency locks, policy, evals, and deployment files with CODEOWNERS and rulesets.
- Separate untrusted build/test from privileged follow-up. Never check out fork-controlled code in a privileged `pull_request_target` job; GitHub Security Lab describes the resulting “pwn request” class ([Preventing pwn requests](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/)).
- Pass PR titles, branch names, issue text, matrix values, and other untrusted contexts through typed inputs/environment variables; never splice them into shell or generated code.
- Do not expose secrets to forked/untrusted jobs. Do not use production environments in verification.
- Use GitHub Environments for deploy approval, branch/tag restrictions, environment-scoped secrets, and prevent-self-review where available ([deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)).
- Require merge-queue checks on `merge_group`, not only `pull_request` ([merge-group trigger](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#merge_group)).
- Treat caches as untrusted across trust boundaries. Partition by repository/ref/lock digest and do not restore author-controlled caches into clean verification.
- Upload only redacted logs. Attest releasable artifacts and verify subject digests before deploy ([artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations)).
- Ensure a workflow cannot modify the workflow/policy that granted its own token and have the modified version take effect in the same approval.

## 5. GitHub App and webhook controls

- Select only required repositories. Use repository Metadata read, Contents as needed, Issues/Pull requests as needed, Checks as needed, and organization Projects permissions only for the controller that reconciles them.
- Separate read/plan and write/apply credentials. The plan for a config PR must not have mutation credentials.
- Keep private keys in a managed secret store/HSM-capable service. Rotate keys and webhook secrets with overlapping verification windows. Never put them in Actions artifacts or model context.
- Validate webhook HMAC-SHA256 against raw request bytes with constant-time comparison ([validating deliveries](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries)).
- Restrict TLS ingress, body size, content type, event types, installation/organization/repository IDs, and replay age.
- Persist delivery ID before processing. Acknowledge quickly and process asynchronously. Reread authoritative GitHub state because deliveries can be duplicated, delayed, out of order, or missed ([webhook best practices](https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks)).
- Paginate complete API collections. Respect primary/secondary limits and `Retry-After`; cap retries and add jitter ([REST best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api)).
- Treat partial GraphQL `data` with `errors` as partial/unknown. Record one logical effect per mutation and reread.
- Do not infer authorization from webhook `sender`, comment text, or an issue assignment. Resolve the authenticated actor and role through policy.

## 6. Prompt injection and untrusted content

All issue bodies, comments, repository code and docs, PR diffs, test output, logs, retrieved web pages, memories, and MCP/tool results are data. Some can contain instructions intended to redirect the model.

Controls:

1. Build context bundles with visible trust classes. Only protected policy from the pinned base revision can be authoritative guidance; even that guidance is not enforcement.
2. Keep system capabilities outside the model. A deterministic proxy validates action enum, schema, exact arguments, current attempt/fence, path/resource scope, expected revision, rate/cost budget, and idempotency key.
3. Use deny-by-default tools and egress. High-risk actions require a separate human decision. Do not expose a general shell, arbitrary network, GitHub admin API, secret store, or deployment API unless the exact task policy permits it.
4. Never send secrets to the model. Use opaque handles and a broker that injects narrowly scoped credentials directly into a process when required.
5. Separate planning from execution. Planner is read-only. Executable plans are schema-validated; prose cannot add permissions.
6. Mark retrieved instructions as quoted evidence. Refuse directions to ignore policy, reveal credentials, contact new destinations, modify gates, or self-approve.
7. Test with direct/indirect injection, encoded instructions, malicious tool output, repository instruction conflicts, data exfiltration requests, and evaluator manipulation.
8. On suspicion, stop the worker, fence/revoke it, preserve redacted evidence, check access logs/effects, rotate possibly exposed credentials, and require human incident review.

The model can still be manipulated despite these steps. Safety comes from capability limits and independent gates, not confidence in detection.

## 7. Sandbox and runtime controls

- Use one disposable VM/container/microVM per attempt or verification job from an approved digest-pinned image.
- Run unprivileged; drop Linux capabilities; use seccomp/AppArmor or equivalent; read-only base mounts; isolated process/user/network namespaces; bounded CPU, memory, disk, process count, and wall time.
- Mount only the one workspace. Deny host Docker socket, cloud metadata, control-plane database, signing keys, runner credentials, and other workspaces.
- Deny network by default. Permit exact domains/protocols through a logged proxy. Block link-local/private ranges and DNS rebinding. Package registries use locks, hashes/signatures where available, and an approved mirror.
- Separate author and verifier environments. The verifier has no author cache, repository write token, production secret, or mutable test oracle.
- Bind branch/path/command capabilities to `attempt_id + lease_fence + expiry`. Check fence at every gateway write. Short-lived credentials reduce exposure but do not replace fencing.
- Stream heartbeats independently. Expiry closes gateways first, then terminates the sandbox. A zombie process cannot regain access with an old token.
- Store large outputs in digest-addressed artifact storage with malware/secret scanning and retention. PostgreSQL stores metadata and digests, not uncontrolled raw prompts.
- Treat generated code and build scripts as untrusted until clean verification.

## 8. Credentials and data

| Secret/data class | Allowed location | Prohibited location |
|---|---|---|
| GitHub App private key, signing key | Managed secret/KMS; controller memory only when needed | Git, model prompt, Actions artifact, worker disk |
| Installation/worker token | Brokered, attempt-scoped, short-lived process environment/file | Logs, checkpoints, reusable caches, issue/PR |
| Webhook secret | Ingress secret store with rotation version | Worker, Git, public diagnostics |
| Production deploy credential | Environment-scoped deploy runner only | Implementation/verifier, model context |
| Sensitive issue/telemetry | Approved private store; redacted reference | Public issue/Project, general prompt archive |
| Approval/event metadata | PostgreSQL and approved immutable export | Mutable label as sole record |
| Raw prompts/logs | Encrypted restricted store with short TTL if needed | Permanent audit record by default |

Scan commits, artifacts, and logs for secrets. A detected credential is assumed compromised: stop affected workflows, revoke/rotate, inventory use, redact presentation copies without destroying required forensic evidence, and open an incident.

## 9. Supply chain and artifact integrity

- Protect dependency manifests and locks. Require dependency review for changes.
- Pin Actions and build images by digest/SHA; record tool and compiler versions.
- Generate SBOM and provenance for releasable artifacts. Bind verifier evidence and deploy approval to artifact digest.
- Do not let a candidate modify its decisive verifier workflow/eval and consume that modified gate without independent protected review.
- Verify downloaded checksums/signatures where ecosystems support them. Use a controlled mirror for high-risk builds.
- Keep baseline and candidate evaluation environments equivalent, and report evaluator/image digests.
- Rebuild or promote by digest, never a mutable tag.

## 10. Fences, replay, and confused-deputy defense

Every mutating request includes actor, work item, attempt, current fence, policy/spec/base hashes, expected resource revision, capability scope, and logical effect key. The gateway verifies all fields against PostgreSQL immediately before the effect.

Record `effect.intent` before the external call. On timeout or crash, the outcome becomes `unknown`; query the remote service for a receipt/state. Retry only if the effect is proven absent or the API is convergent under the same key. A late worker result is logged as stale and cannot transition state.

GitHub assignments and Project updates are not atomic compare-and-swap lease primitives. The database transaction and fencing token provide exclusivity. GitHub Actions concurrency is not a substitute because it permits limited pending state, replacement, and arbitrary ordering ([concurrency behavior](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)).

## 11. Approval and exception security

Approvals bind verified principal/role/quorum to exact content digest, risk, action scope, and expiry. Recompute at every consequential boundary. New commit, material spec/policy/eval change, role loss, or expiry invalidates the approval.

An exception must contain:

- affected invariant/check and exact SHA/artifact/environment;
- business/incident reason and named independent approver;
- bounded action, duration, and blast radius;
- compensating controls and rollback;
- evidence and mandatory follow-up/review.

Exceptions cannot grant an agent authority to change the exception policy, approve itself, expose unrestricted secrets, erase audit evidence, or convert an unknown effect into success. Break-glass revokes normal automation in the affected scope and should require two people where feasible.

## 12. Self-improvement ceiling

Automatic behavior may collect metrics, cluster failures, draft proposals, generate candidate patches/prompts, run already-approved evals offline, shadow without effects, and operate within a preapproved narrow canary envelope. It may automatically roll back on a predefined guardrail.

It may not autonomously:

- change risk classification, approval quorum, permissions, secret/egress classes, sandbox boundary, rulesets, CODEOWNERS, evaluator/oracles, promotion threshold, or retention/audit policy;
- add or weaken evaluation cases to favor itself;
- move from shadow to canary or broaden a canary;
- approve an exception, production deployment, or general promotion;
- hide, rewrite, or select away adverse evidence.

Promotion requires an independent human approving the exact candidate, evaluation, and rollout digests. This is the maximum safe self-improvement boundary for this design.

## 13. Required security tests

Before any production pilot, demonstrate in an isolated environment:

- invalid/missing webhook signatures and duplicate/out-of-order deliveries do not cause unauthorized effects;
- two dispatchers cannot create two active leases; an expired fence cannot write;
- lost acknowledgments do not duplicate PR, branch, comment, merge, deploy, or deletion;
- malicious issue/code/log/action output cannot expand tools, egress, secrets, paths, or approval;
- fork PR workflows cannot access write tokens/secrets or poison privileged verification;
- a new push invalidates approvals and evidence; a check for another SHA is rejected;
- ruleset/CODEOWNERS/App-permission/eval/policy modifications need independent exact-head review;
- verifier is clean, network/secret constrained, and independent of author state;
- credential rotation, kill switch, controller compromise, database restore, and signing-key rollover runbooks work;
- self-improvement cannot curate, approve, promote, or widen its own candidate.


## 14. Multi-repository product isolation

A control-product installation is tenant-scoped by immutable repository and GitHub App installation IDs. Include that tenant in database authorization, queues, effect/idempotency keys, artifact encryption context, caches, traces, quotas, token requests, and kill switches. Do not authorize cross-repository access from user-supplied names or Project links. Cross-repository workflows need explicit allowlists and approval from every affected repository owner.

Configuration inheritance cannot weaken product/organization mandatory denies, approval separation, secret/egress boundaries, audit, or minimum compliance controls. Upgrade PRs show permission and effective-policy deltas. Release pins use immutable digests with compatibility declarations and rollback pins.

Privacy filtering happens inside the consumer boundary before outcome export. Free text and identifiers are denied by default. Evaluation-case contribution requires human review for provenance, consent/license, data class, redaction, and retention. The product repository's dogfood tenant uses stable promoted code to judge candidates; candidate code receives no release, promotion, or self-install authority.

Engineering and any future GTM domain use separate domain packs, repositories/tenants, connectors, credentials, graders, approvals, and compliance policy. Shared runtime code does not grant cross-domain data or action access. GTM remains future scope and is not delivered here.
