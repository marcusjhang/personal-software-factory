# Reference: archdev's software factory ("A Look Inside the Factory")

**Source:** Calvin Grunewald, *A Look Inside the Factory*, The Building Machine, 19 Nov 2026.
<https://thebuildingmachine.com/p/a-look-inside-the-factory>

**Why this is here:** Marcus wants psf improved using the whole article, not only a task list (after finals, from
1 Dec 2026). This page is the reference for that plan. It paraphrases the article section by section, keeping its
specifics. It does not reproduce the article's text or its config block; read the original for exact wording. The
last part records how psf v0.2.1 compares, and the gaps that the plan will start from.

Status: reference only. No psf behaviour changes with this page. The improvement plan is separate and comes after
1 Dec; it will be built only in sessions Marcus joins (no auto-building).

---

## 1. Thesis and origin: vibe-coding a harness

- **Question behind it.** Which moats do AI companies have? Base models commoditise as intelligence gets cheaper, so
  could the agent harness be the moat? The author's answer is no: software on its own is not a moat. He built a
  harness in June 2026 to test how hard one is to copy. It was not hard.
- **26 Jun 2026: spec by research.** Codex researched the most-used Claude Code features and wrote a spec. Core:
  UX, agent loop, tool calling, skills, AGENTS.md, images, MCP. Newer: monitors, loops, workflows. Tool calling held
  the hard details (foreground versus background shell, subagents, steering messages).
- **Scoping.** Codex ranked about 30 features. He cut anything skills or shell tools already cover (browser
  automation, sandboxing, voice) and all enterprise features. Where Claude Code and Codex differ (CLAUDE.md versus
  AGENTS.md) he took the Codex convention, because third-party harnesses were converging on it.
- **Task CSV as the harness.** The features became small tasks in a CSV: each row had acceptance criteria and
  dependencies, plus two empty columns, DONE and implementation notes. A `/goal` run worked the CSV:
  - every task shipped with tests and had to pass type, lint and test gates before its commit;
  - one commit per task, an "x" in DONE, and a progress-journal entry for each decision.
- **Result.** About two days (evening of 27 Jun to morning of 29 Jun): 146 commits, 130 of 188 tasks done. (A figure
  caption says 130 task commits; the article does not reconcile 130 and 146.)
- **Key trick:** real PTY tests that drive the terminal UI. That is what made unattended progress possible.
- **Bugs** were small and found by use (skills not injected, token caching). After fixes the harness was at rough
  parity with Claude Code, worked with any model, and was extensible. Named Astrodev, renamed archdev in August.

### Factory mode (11 Aug)

One short, casual prompt added "factory mode":
- the main chat becomes the **overseer**; an optional side panel lists workers and their tasks;
- the TUI spawns worker subprocesses, which ask the main process for work; ready tasks go first come, first served;
- workers heartbeat so the UI shows what each is doing;
- workers submit finished work to a daemon with `archdev push`; the mode is turned on with `--factory`.

Another harness fixed the first factory; after that the factory was good enough to fix and improve itself.

## 2. The architecture: goal in, pull requests out

Four stages:
1. **Human → overseer.** The human gives the overseer (or a local agent session) a goal and approves the plan.
2. **Overseer → tasks.** The overseer turns the plan into tasks (stored in the cloud so more factory nodes can
   share them) and hands ready tasks to workers.
3. **Workers.** Each worker codes in its own git worktree and pushes to a **private remote on the human's
   machine**, where the human's configured rules and workflows run first.
4. **Daemon.** Runs those rules and workflows on each change and pushes to GitHub only once they pass. It then
   watches the PR and fixes review comments, CI failures and merge conflicts until merge.

The human touches a task twice: describing the goal and approving the plan. After that it runs unless a question
comes up, and he can auto-merge. Once a worker pushes, the worker is done; the daemon owns the work.

## 3. Design points

The author frames these as decisions accumulated over time: vibe-coded systems build design debt, which later
iterations pay down.

### 3.1 The task, not the plan or prompt, is the unit of work

Long plans and verbose chat output suffer context rot; reliability drops the further the agent gets. Tasks win
because they are:
1. easier to review than a long plan, especially visually;
2. independently and automatically verifiable;
3. one PR each, which is easier to review than stacked PRs (agent-made stacked PRs hurt productivity);
4. a better fit for a context window;
5. DAG-shaped, which suits a workflow runner.

- **Local web view.** Reviewing tasks in the TUI was hard, so the overseer serves a localhost page that streams to
  and from it, showing tasks and DAGs. "A coding agent launches a live web page" became a pattern he reuses.
- **Epics.** Each submitted task DAG is an epic with a progress view that flags stuck tasks (usually waiting on
  something external: a deploy, a secret) and guides unsticking. Example: 33 of 41 done, 4 stuck, paused tasks
  under "Needs you".
- **Plan approval is version-bound.** Approval covers one exact plan version. Any note makes the overseer revise,
  and the new version needs a new approval. The plan-review page shows each task's risk and the decisions the plan
  needs from the human.

### 3.2 Interactive versus non-interactive processes

Two long-lived processes:
- **Overseer** (interactive, in the terminal). The human can talk to it, but its main job is reviewing workers as
  an adversary. In automatic mode it keeps workers on track itself; in manual mode it hands anything a worker needs
  to the human.
- **Daemon** (headless). Three jobs: pre-push adversarial review; keeping PRs always merge-ready with no
  babysitting; extensibility to new workflows and job types.

Overseer and workers only build tasks. The daemon (designed 7 Aug, four days before factory mode) is a local git
server plus workflow engine: `archdev push` sends work to a private bare repo, each push becomes a durable SQLite
job, and each job runs against the exact commit in a throwaway worktree. Nothing reaches GitHub until lint, tests,
policy checks and review pass on that exact commit.

Why split them: (1) the human-in-the-loop style is chosen independently of the standard adversarial pre-push
workflow; (2) tension between parts (overseer versus worker, worker versus the daemon's multi-agent review) gives
better results.

### 3.3 Every process gets exactly one supervisor

A cluster of bugs in one area convinced him it was an architecture problem ("enough bugs in one area" means the
design is wrong). He added one supervisor per group of similar subprocesses, with a shared supervisor/child
abstraction. It fixed three things:
1. runtime state is no longer fragmented: each supervisor is the source of truth for its group;
2. failure handling is clean: a supervisor restarts children, and stopping a process kills its whole group;
3. orchestration lives in one place, which made cross-cutting problems such as GitHub API rate limits easy to fix.

The workers panel now shows model state separately from worker health, so a quiet model no longer looks like a dead
worker.

### 3.4 Separate mechanism from policy, and evals become cheap

Borrowed from OS scheduler design: the mechanism (switching the CPU) must be fast and correct; the policy (which
process next) can change without touching it.

- **Daemon = mechanism:** responding to git hooks; claiming and managing jobs against exact commit SHAs; workflow
  management, with workflows defined in JSON; observability.
- **Policy = each repo's `archdev.json`.** Every workflow step is a prompt plus a model alias.

The trimmed monorepo config, described structurally:
- `factory`: 10 workers; model alias `@factory-automation` for the overseer and `@factory-worker` for workers.
- `publish`: auto-publish on, with its own model alias for PR metadata.
- `pipeline_bindings`: branch update → `branch-validation`; PR feedback → `address-pr-feedback`; PR rebase
  conflict → `resolve-pr-rebase-conflict`.
- `branch-validation`: `lint` (affected packages against origin/main), `policy` (branch policy checks), `test`
  (related tests, 900-second budget), then `review` via `review-and-fix`. Lint, policy and test are
  continue-on-error: they **fail open into review**, so the fix agent repairs them.
- `review-and-fix`: a team review of the branch commits, then a fix agent that reads that output; then commit, a
  final review, and up to two more fix/review rounds.
- `pull_requests.automation.ci_failures.infrastructure_log_patterns`: regexes that mark a CI failure as caused by
  the runner, not the code (the example matches a request timeout).

If policy lived in code, every review tweak would be a daemon change, risky and slowed by compile, lint and tests.
So the daemon stays small and policy lives in config.

### 3.5 Replay evals

- Freeze real findings from past PRs, each with its PR head and a reference fix.
- Replay the fix step in a sandbox; an independent grader checks each finding was fixed and that nothing regressed.
- Each experiment is an **arm**: a small JSON overlay on the fix step's config. Examples: `b-reproduce-first` adds
  one prompt line asking for a failing test before the fix; other arms swap the model, add a lint gate, or ask for
  findings as JSON.

Run of 20 Oct 2026, six arms over 19 graded cases (9 high, 14 medium findings):

| Arm | High fixed | Medium fixed | Regressions | $ per fixed high |
|---|---|---|---|---|
| a-current (the live config) | 9/9 | 14/14 | 0 | 2.98 |
| b-reproduce-first | 9/9 | 14/14 | 0 | 3.09 |
| e-self-check | 9/9 | 14/14 | 0 | 2.99 |
| f-json | 9/9 | 13/14 | 0 | 2.72 |
| d-sol (cheaper model) | 9/9 | 13/14 | 0 | 0.85 |
| d-grok47 | 7/9 | 13/14 | 2 | 2.81 |

- No arm beat the current config on accuracy.
- The cheaper model was about 3.5x cheaper per fix, but on one case it should have declined, it deleted the public
  wrapper the reviewer had objected to. **Cost wins can hide destructive behaviour.**

## 4. Where the human enters the loop: six rounds of taming questions

The original goal was to automate everything between planning and clicking merge. That failed: real software needs
external dependencies, vendor and production data, QA and credentials, so agents need a human at some points unless
they hold every key. Agent-written plans are also ambiguous or wrong in places, and details shift once a worker is in
the code; more upfront planning wastes the agents' ability to solve problems. Running 24/7, the overseer kept
blocking on him. Six rounds fixed it:

1. **Aug:** plan approval moved from chat to the browser (the version-bound approval above).
2. **Early Sep:** the overseer reported "blocked" to his terminal multiplexer (Herdr). It fixed nothing, but showed
   which session needed him.
3. **17 Sep:** `factory.autonomy` = `confirm` (default; ask before each call) or `auto` (follow a playbook to
   unblock workers; may apply a task graph without him while no major decision is open). By 28 Sep `auto` had never
   blocked on him. `/autonomy` switched modes mid-session from 30 Sep.
4. **30 Sep: questions became paused tasks.** Before, a question was a chat message nobody saw: the overseer had
   paused tasks 67 times without telling him, and answers never reached the next worker, whose prompt came only from
   the task's name and description. Now a question is a paused task with: pause kind (needs a decision, needs access,
   or spec doesn't match the code), the question, why the worker stopped, and a recommended answer. His answer is a
   task comment; the task reopens and the next worker sees the answer in its prompt.
5. **30 Sep: escalation limited to six categories.** On 28 Sep workers had sent 151 decision requests in about 21
   hours, many they could decide themselves (example: whether to make a temporary base-commit checkout for a
   comparison). Only six kinds go to the human: **credentials; spending; live infrastructure (merging counts);
   irreversible actions; product decisions; anything the task marks for sign-off.** A question must name one of the
   six or the overseer rejects it; everything else the overseer decides and records the reason on the task. Every
   question carries a recommended answer, so the human reacts to a proposal.
6. **Oct: one "Needs you" surface** wherever he already looks: a TUI tab, the web tasks page, the CLI, his phone, a
   daily digest. PRs the daemon gave up on land there too. A bell badge counts everything waiting; items sort into
   agent asks, questions, checks, stalled and paused tasks. "Catch up" walks through items one at a time (45 in the
   example), e.g. a task paused 22 days with no recorded reason that nothing would ever resume (one keystroke to
   resume, close as done, or cancel); a question waiting 8 days on four live Slack changes; a worker's 401 from a
   production API asking for access, with a recommendation.

## 5. Results, compute and what's next

- **Throughput:** 1,940 factory PRs merged into the monorepo since 21 Aug, running 24/7 including holidays.
  Weekly merged PRs from the week of 17 Aug: 14, 53, 41, 100, 143, 120, **251** (peak, week of 28 Sep), 210, 163,
  218, 240, 91, 139, and 157 in the first four days of the week of 16 Nov (the values sum to 1,940).
- Keeping a DAG-running factory full means many things in parallel, which he sees as general to agentic
  development.
- **Hardware:** an M5 Max with 128 GB ran only 4 workers plus 4 daemon jobs and stalled with his interactive Claude
  Code sessions alongside. The factory moved to a System76 AMD laptop (8 cores / 16 threads, 64 GB); then work
  throughput became the limit. A multi-node epic added task leasing; it now runs on two machines, still short of
  compute. CI and token spend also break at this pace.
- **Next:** moving fully to the cloud. Open questions he raises without answering: what authoring a PR means when a
  machine turns tasks into PRs; why tasks should be assigned to anyone but the bot; who is responsible; what
  engineers do.

## 6. Lessons (gathered from across the article)

- The task is the right unit; agent-written plans are ambiguous and change once workers code.
- Adversarial review is a design principle: overseer versus worker, worker versus daemon.
- Bugs clustering in one area signal an architecture problem (this produced the supervisors).
- Separating mechanism from policy makes evals cheap and safe.
- Autonomy needs explicit escalation rules, or the human becomes the bottleneck; the overseer must decide what it
  can and surface only the human's decisions, each with a recommendation.
- Stuck tasks usually involve external dependencies (deploys, secrets, access) and do need a human.
- At scale, compute, CI and tokens become the bottleneck.

---

## 7. psf v0.2.1 compared (Top, 20 Nov 2026)

**psf is stronger on trust and governance:** hash-chained ledger, digest-bound approvals, verify quorum of 2,
governed human-gated improvement (`psf improve`), and the cross-repo feedback loop. **archdev is stronger on
throughput:** task DAGs, parallel workers, and owning the PR until merge.

Starting gaps, in Top's suggested order (to be challenged, reordered or cut in the plan):
1. **Goal → task DAG** (`psf plan`): small tasks with acceptance criteria, one PR each, one approval for the whole
   graph bound to its digest.
2. **PR shepherd** (`psf watch`): fix CI, answer review comments, resolve conflicts; classify infra versus code
   failures.
3. **Parallel workers** (own worktree each, DAG order) with one supervisor per process group; cap around 4 on
   Marcus's Mac.
4. **Fixed escalation categories** replacing hitl/yolo; archdev's six map to Marcus's L3 and Never tiers; everything
   else decided and logged in the ledger.
5. **Questions as paused tasks** with a recommended answer, answers persisted for later workers; feed the Home app's
   Needs you view.
6. **Replay evals** from real OCR findings on Marcus's projects, graded fixed plus no regression, compared on cost per
   fix; this widens `psf improve` beyond numeric policy. Regressions = 0 is a hard gate.
7. **Every pipeline step as config** (prompt plus model alias in `factory.yml`), so eval arms are overlays.

**Not worth copying:** the cloud move and the 10-worker scale.

**Keep** psf's strengths through every change: hash-chained ledger, digest-bound approvals, verify quorum,
governed improvement. Each change in the plan gets its own eval design.
