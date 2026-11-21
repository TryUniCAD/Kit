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
