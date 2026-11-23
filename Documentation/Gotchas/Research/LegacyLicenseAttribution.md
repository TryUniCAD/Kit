<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Historical notice attribution must match exactly

## Expectation

The Python comment policy preserves complete legal notices required by workspace instructions.

## Actual behavior

The checker recognized only the later contributor attribution.
It rejected the earlier `Parashell, Odin Glynn-Martin` notice required by the original workspace instructions.

## Workaround

Preserve the required notice without modifying its text.
The checker recognizes both complete historical notices only at the start of a file, after an optional shebang.
Altered or misplaced notices remain comment-policy violations.
Process coverage in `tests/Policy/LegacyNoticeTests.py` checks both valid attributions and rejection cases through the actual steering command.
