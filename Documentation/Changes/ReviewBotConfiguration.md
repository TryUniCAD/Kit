<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Review configuration and skill activation

## Problem

Review instructions duplicated the provider mention and trigger across several files.
A reviewer change required multiple edits.
The skill also exempted edits to itself from activation.

## Change

The single request value is `Comment` in [ReviewBot.json](../../.agents/skills/standard-pr-practice/ReviewBot.json).
Other guidance links to that file.
Agents load the value before requesting review.
They submit it once per accepted head unless that head already has a request or review.

[AGENTS.md](../../AGENTS.md) and [CLAUDE.md](../../CLAUDE.md) require skill activation for every repository task.
This includes investigation, documentation, and skill edits.
Activation applies relevant instructions but does not grant additional publication or merge authority.

## Evidence boundary

Verify reviewer identity, reviewed SHA, findings, approval, CI, and enforced requirements separately.
Changing the request does not install an app or change provider settings.
It does not modify CODEOWNERS, CI exclusions, or branch protections.
See [the queue guide](../../MergeQueue.md) for those separate controls.

## Recorded verification

The original change inspected the instruction diff and searched for duplicated trigger literals.
No local tests ran.
Remote PR CI verifies policy and skill structure.
Merge-group acceptance remains separate from PR evidence.
