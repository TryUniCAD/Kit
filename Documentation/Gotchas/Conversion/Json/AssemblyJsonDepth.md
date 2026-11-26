<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Deep assembly JSON must reopen

## Expectation

The JSON reader reopens linked assemblies within the nesting range supported before decoder optimization.

## Observed behavior

At PR #284 head `2a24f685942c3f132fa3fc7414cb164d2fec1904`, a 100-level assembly saved successfully on Python 3.14.7.
Reopening that JSON raised `RecursionError`.
Typed-record and tagged-container helpers retained additional frames while decoding their children.

## Resolution

Resolve each record type before child traversal.
Construct each tagged container after child traversal.
Keep the single root wire validation and the existing interpreter recursion limit.

The public codec regression checks canonical JSON and the embedded leaf document.
It exercises 80 levels on Python 3.11 and 100 levels on later supported runtimes.
These checks establish JSON compatibility, without qualifying native CAD conversion.
