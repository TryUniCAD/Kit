<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Review bot configuration and required skill activation

Review request instructions previously duplicated a provider-specific mention and
comment across agent guidance, skill metadata, and follow-up examples. Changing
reviewers required editing multiple files, and the skill exempted its own edits
from activation.

The Reviewers array in
[ReviewBot.json](../../.agents/skills/standard-pr-practice/ReviewBot.json)
defines reviewer identities, required native reports, and exact top-level
requests. Agents reload it before requesting review and submit each configured
request verbatim once per accepted head unless that reviewer already has a
request or review. Each configured reviewer must pass its listed reports and
submit a current-head approval. The previous request mentioned a regular GitHub
user and did not invoke the installed review app.

Both [AGENTS.md](../../AGENTS.md) and [CLAUDE.md](../../CLAUDE.md) require activating
[standard-pr-practice](../../.agents/skills/standard-pr-practice/SKILL.md) before
every repository task, including investigation, documentation, and skill edits.
Activation applies relevant instructions without granting additional publication
or merge authority.

Reviewer identity, reviewed SHA, findings, approval, CI, and enforced repository
requirements remain independently verified. This change does not install an app,
alter provider settings, modify CODEOWNERS, change CI exclusions, or update live
branch protections. Existing provider configuration is documented separately in
[the queue guide](../../MergeQueue.md).

Verification: inspected the complete instruction diff and searched maintained
workflow guidance for duplicated trigger literals. No tests ran locally; remote
PR CI provides repository policy and skill verification. Merge-group acceptance
remains deferred until authorized queue enrollment.
