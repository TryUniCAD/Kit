<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Terra builder generation

New automatic builder-development jobs using `--advisor codex` select
`gpt-6.1-terra` when `--model` is omitted. The saved `BuilderJob.json` pins that
model for the initial generation and subsequent repair calls. An explicit
`--model` remains authoritative. Resuming an existing job preserves its original
model and immutable evidence.

Use the existing ChatGPT login with `--advisor codex --auth login`. This change
does not add an API-key requirement or enable automatic development by default.
Other advice commands and other providers retain their existing model selection.

The bounded offset-plane scope, independent qualification gates and native host
requirements remain as described in
[automatic builder development](AutomaticBuilderDevelopment.md).

Verification prepares fresh jobs through the real campaign command, checks the
saved default and explicit model selections, and checks that resume preserves
the saved model. These preparation checks do not establish native qualification.
