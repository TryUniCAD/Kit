<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Preserve explicitly required historical legal notices

## Expectation

A file with the exact legal notice required by the workspace should pass the code-comment policy.

## Actual behavior

The steering checker recognized only the later three-contributor copyright line.
The original workspace-required notice named Parashell and Odin Glynn-Martin.
Its complete leading notice was therefore reported as seven prohibited code comments.

## Resolution

The checker recognizes both complete, exact legal notices at the start of a source file.
It still rejects partial notices, changed legal language and unrelated comments.
Existing copyright text is preserved.
A process scenario runs the actual steering CLI against both notices and two malformed controls.
