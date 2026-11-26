<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# CAD catalogue CLI

Use `kit run --root .` with the `fusion` or `solidworks` format and its catalogue.
Specify a new output directory.
The command launches the existing catalogue batch and its private supervisor.
The [research CLI guide](../../../Tasks/ResearchCommandLine.md#run-a-cad-catalogue-with-optional-advice)
lists command examples and sign-in modes.

The optional advisor receives a bounded description when a supported inference job stalls.
The Codex and Claude modes use the installed vendor CLI.
Ollama sends structured requests to the loopback service.
The supervisor checks the job's evidence receipt before and after each request.
The batch records proposals separately from deterministic results and never executes model output.
Only catalogue entries with reviewed routes can run.

Task `CatalogueCli` extends the A10 advice path in PR #158 and the batch runner in PR #168.
The scoped exit condition is one CLI invocation per provider mode with deterministic receipts and separate advice records.
Native CAD qualification and unattended pilot acceptance remain in their existing programme steps.

## Verification

Eight local process cases passed, including the four cloud provider and authentication combinations with disposable executables.
A local loopback fixture accepted an Ollama request and returned a saved proposal for a synthetic paired gap.
A live Codex run using saved ChatGPT sign-in returned a proposal for the same class of synthetic gap.
Live Claude, API key billing, and local model generation remain unverified.
