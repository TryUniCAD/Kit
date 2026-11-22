<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Builder generation optimizations

Codex builder jobs keep one controller-owned app-server connection across their
short-lived generation workers. Each request uses a fresh ephemeral model
thread, the pinned model, low reasoning, a bounded JSON schema and compact base
instructions. The default remains GPT-6.1 Terra through the existing ChatGPT
login. No API key is required. Other providers retain their existing transports.

The controller closes its provider on completion, pause or failure. It retains
ownership evidence when cleanup cannot be verified. Resume preserves stale
endpoint evidence only after proving that the old controller is gone or its PID
has been reused. An uninspectable or live owner cannot be displaced.

Workers verify the controller identity and complete a mutual HMAC challenge
before sending a prompt. The private broker token never crosses the socket,
and a reused local port cannot obtain a request without proving ownership.

## Request coalescing

New jobs sharing the same builder registry also share its `Generation` candidate
cache. A process-released per-request lock covers the provider reservation,
generation, accounting and publication. Concurrent identical requests therefore
consume one model call. A reused candidate receives fresh artifacts in its own
run directory and records zero additional provider usage.

Cache identity includes the complete approved discovery packet, configured
model, authentication mode, schema, generation source hashes, provider identity,
personal-instruction hashes and instruction authorization. Changed diagnostics,
models, source, schemas or instructions require a different entry. An existing
corrupt entry is retained and blocks reuse without repeatedly spending calls.

Candidates in this cache are explicitly unqualified. Every run still needs its
independent native verification, reserved qualification and accepted receipts.
The existing qualified-builder registry remains the first reuse path.

## Personal instruction authorization

Codex app-server can include global `AGENTS.md` instructions from its existing
profile even when project documentation is disabled. Builder generation refuses
to send those instructions unless the fresh job explicitly selects
`--builder-personal-instructions`. This authorization is saved in the job and
cannot be changed by a worker or a resumed command. Project instruction discovery,
automatic skills, tool execution, MCP servers and hooks remain disabled.

The `codex exec --ignore-rules` option controls execution-policy rules; it does
not establish that global `AGENTS.md` instructions are absent. Global instruction
context must not be confused with the discovery recipe or with native acceptance.

## Verification boundaries

Process integration exercises real workers, local authenticated broker sockets,
concurrent cache users, independent run directories, interruption recovery and
bounded protocol failures. A fixture model response proves transport and
accounting behavior only. It never establishes native builder qualification,
complete decoding or conversion. Live-provider timing and native application
acceptance remain separate evidence.

At source `803f5a4bfc038b1e59f0528f821fab30835dfdf8`, an explicitly authorized
live GPT-6.1 Terra check used the same offset-plane recipe and retained its
global instruction authorization. The initial call took 3.794 seconds; a second
call over the same provider process took 3.200 seconds. Reusing the identical
cached candidate took 0.00330 seconds and consumed no provider reservation or
tokens. The second live call used a separate cache namespace solely to measure
the warm transport rather than another cache hit.

Both live calls returned the same schema-valid program, with 6,519 input tokens
and 32 output tokens each. This is 43.3% fewer input tokens than the earlier
11,491-token Terra CLI smoke check. The provider process was retained between
the calls, then closed and confirmed absent. There were two model reservations
for two live calls, with no reservation for candidate reuse. These are individual
timing samples, not a latency guarantee or native acceptance evidence.

Seventeen independent process checks passed against this generation source,
including concurrent separate-run requests consuming one provider turn and one
reservation, request invalidation, interrupted owners, corrupt-cache refusal,
authenticated broker boundaries and expired deadlines. The transport client and
cleanup changes also have separate real-process coverage documented in their
linked change entries.

Across focused runs, all 48 builder-development process cases passed. Two
inherited supervisor transport fixtures required explicit fixture-only CPU and
memory reservations because this host could not admit their workers above the
production reserve. Production reservations, worker limits and assertions were
unchanged; see [worker fixture resources](WorkerTransportFixtureResources.md).
Fresh command preparation also verified both instruction-authorization choices
and that resume preserves the saved choice without a model call.
