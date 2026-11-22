<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Persistent Codex generation transport

The research generation client can retain one owned `codex app-server` process
across multiple bounded requests. Each request starts a fresh ephemeral thread,
uses its explicitly pinned model with low reasoning, validates the selected model
and read-only permissions, and unloads that thread after completion. A new model
session never inherits a previous candidate's conversation.

The controller owns the client lifetime. Closing the client also cancels an
active request and terminates its owned process group or Windows job. It does
not run a detached provider daemon or change the user's Codex home or login.
The client uses the existing ChatGPT login without copying authentication data.

Compact base instructions replace the generic coding prompt. Shell execution,
apps, plugins, delegation, images, hooks, memories, goals, code mode, browsing and
MCP servers are disabled. Automatic skill-catalog instructions and project
instruction discovery are disabled. Unexpected tool requests and tool items
fail closed. Global personal `AGENTS.md` files are independent of Codex's project
instruction byte budget; when Codex reports such files, the client blocks before
starting inference rather than silently exporting extra personal context. Only
the controller's explicit `AllowPersonalInstructions` opt-in permits these global
files; request payloads cannot grant that permission. Codex's `--ignore-rules`
flag concerns execution-policy `.rules` files and does not omit global
`AGENTS.md` instructions.

Initialization, model lookup, thread creation, generation and thread unloading
share one request deadline. Protocol output and stderr retention each have a
4 MiB bound. The client accepts partial JSON lines, retains correlated protocol
events and actual reported token usage, and rejects malformed responses, model
substitution, changed permissions, unexpected instructions and incomplete turns.
No provider failure silently falls back to another model or transport.

`CodexIdentity` supplies bounded local hashes of the resolved executable and
global instruction candidates, plus the installed npm package version when
available. It does not read tokens, start an app-server or make a model call.
Callers can include these pins when deciding whether a generated candidate can
be reused. Candidate reuse remains separate from native qualification.

Nine real process-protocol checks cover process reuse with separate ephemeral
threads, split message framing, timeouts, excessive output, unsolicited tool
requests, model substitution, personal-context rejection, owned descendant
cleanup and concurrent cancellation. The available macOS host's real app-server
preflight confirmed the requested model and read-only policy but reported global
personal instructions, so inference was blocked. Automatic approval also
rejected a live follow-up because that context was outside the approved request.
No successful live inference, native qualification or latency improvement is
claimed by these client checks.
