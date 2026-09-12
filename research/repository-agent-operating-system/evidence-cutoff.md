## Intended evidence-scope cutoff and legacy date metadata

The intended evidence-scope cutoff is **`2026-09-12T23:59:59Z`**. It is a decision-scope boundary only. It does not establish when the checked-in legacy sources were retrieved or whether that corpus complied with the cutoff.

Every `2026-09-13` value in the legacy results or evidence index—including values labeled `as_of`, `access_date`, “accessed,” “observed,” or similar wording—is **unverified legacy local-calendar metadata**. The earlier account that associated those dates with a UTC+08 host and an approximate UTC execution window is an unverified process narrative, not evidence. No actual UTC retrieval time, pre-cutoff retrieval, or cutoff compliance is asserted for the legacy corpus.

Legacy compliance remains **unverified** because the corpus lacks the per-source immutable observations required to prove collection history. A fresh immutable re-fetch must record actual UTC `retrieved_at` values, run identity, content or response digests, snapshot lineage or a signed unavailability reason, redirects and status, validator output, and human semantic-review dispositions. Until that blocking gate passes, the dates above must not be used as retrieval proof or as evidence that mutable content matched its state at the intended cutoff.

See the [`research-manifest.json` provenance disclaimer](./research-manifest.json), [`evidence-repair.md`](./evidence-repair.md), and [PLAN §4](../../PLAN.md#4-evidence-and-method) for the controlling provenance limits and repair gate.
