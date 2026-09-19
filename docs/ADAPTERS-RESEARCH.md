# Harness adapters — how others solve it, and our fix

Research (fetched 2026-09-19) on how established open-source/proper agent systems
abstract over coding harnesses and normalize **permissions**:

- **Agent Client Protocol (ACP)** — <https://agentclientprotocol.com/protocol/overview>
- **Cline** (Apache-2.0, 68k★) — <https://github.com/cline/cline>
- **Codex CLI** (Apache-2.0, 125k★) — <https://github.com/openai/codex>
- **OpenHands** — Docker runtime — <https://docs.all-hands.dev/usage/architecture/runtime>

## The problem, restated

We run the same factory across Claude Code, opencode/DeepSeek, and Codex, but each
harness exposes **different** autonomy/permission knobs:
Claude `--permission-mode acceptEdits` + `--allowedTools`; opencode `--auto`;
Codex `--sandbox read-only|workspace-write|danger-full-access` +
`--approve-for-me`/`--dangerously-bypass-approvals-and-sandbox`. Same factory,
different safety posture — not clean.

## How the field solves it

| System | Mechanism | Lesson |
|---|---|---|
| **ACP** | JSON-RPC. `initialize` **negotiates capabilities**; `session/prompt`; `session/update` streams progress; `session/request_permission` asks the **client** to authorize a tool call; `session/cancel`; `session/set_mode`. | The clean answer: **capability negotiation + permission as a request to the host**, not a per-harness flag. |
| **Cline** | Multi-provider; **Plan vs Act** modes; **auto-approve** toggles per edit/command; `.clinerules`; SDK plugins/hooks; headless `--json`. | Separate *mode* (plan/act) from *approval policy* (ask / auto-approve). |
| **Codex** | Explicit **sandbox modes** and **approval policy** as separate axes; `--json` events; `-o` last message. | Model permissions as a small closed enum with a sandbox axis and an approval axis. |
| **OpenHands** | Docker sandbox runtime; action/observation event stream; provider abstraction. | Isolation is a runtime concern; keep the agent interface narrow. |

**Consensus:** define a **normalized autonomy/permission model** in the orchestrator
and *map* it to each harness; advertise **capabilities**; where possible speak a
**standard protocol** (ACP) so permissions/streaming/cancel are uniform.

## Our fix (implemented)

1. **One normalized permission profile** — `safe | workspace | full` — set in
   `runnerOptions.permissions` (factory.yml) or `--permissions`, mapped per harness:

   | profile | claude | opencode | codex |
   |---|---|---|---|
   | `safe` | `--permission-mode default` + read-only tools | (no `--auto`; read-only intent) | `--sandbox read-only` |
   | `workspace` (default) | `--permission-mode acceptEdits` + tools | `--auto` | `--sandbox workspace-write` |
   | `full` | `--dangerously-skip-permissions` | `--auto` | `--dangerously-bypass-approvals-and-sandbox` |

2. **Capability manifest** — `adapters.common.capabilities(harness)` advertises
   `{sandbox, approvals, steering, streaming, acp}` so the controller can reason
   about what a harness supports (mirrors ACP `initialize`).

3. **Where we'd go further (phase 2):** speak **ACP** for harnesses that expose it
   (opencode has `opencode acp`) to get `session/request_permission`, streaming
   `session/update`, and `session/cancel` uniformly — replacing per-harness flags
   with one protocol. Codex (`codex exec --json`, `codex app-server`) and Claude
   (Agent SDK) would each get thin ACP shims.

## Why not adopt ACP today

ACP is the right long-term seam, but it is an editor↔agent protocol; wiring it
means implementing a JSON-RPC client and session lifecycle, and not every harness
speaks it yet. The profile + capability manifest gets parity **now** with no new
dependency, and leaves the door open to swap the transport for ACP later. This
mirrors how Cline started (provider flags) before adding an SDK.

## Evals

Adapter suite **A1–A6**: protocol seam · full loop via external harness · command
construction · prompt passthrough · **permission-profile mapping (A5)** ·
**capability manifest (A6)**.
