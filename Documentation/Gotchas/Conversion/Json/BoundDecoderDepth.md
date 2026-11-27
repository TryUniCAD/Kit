<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# A keyword-bound decoder reduces Python 3.11 assembly depth

## Expectation

Sharing decoder metadata must preserve the previously supported linked-assembly nesting depth.

## Observed behavior

PR #286 head `63433c7a28b477032973361a91835c7b8a6103eb` bound the cache with `functools.partial` before recursive record construction.
On CPython 3.11.15, that callback consumed additional recursion capacity for every nested record edge.
A valid chain containing 75 embedded assemblies raised `RecursionError` through the public JSON reader.
The same chain passed against main `625bdbf9efa35d0fdc4939c59f68561aa927db4b`.
The automatic [review finding](https://github.com/TryUniCAD/Kit/pull/286#discussion_r4678549576) identified this regression.

## Resolution

Pass the unbound child decoder and its cache as separate arguments.
The record decoder calls the function directly with both values.
Keep type lookup outside recursive construction.
Do not increase the interpreter recursion limit.

The [public compatibility case](../../../../tests/Interchange/Compatibility/DecodeDepthTests.py) reopens the 75-level assembly and compares canonical JSON.
The repaired path passed on CPython 3.11.15 and 3.14.7.
This check does not establish unlimited nesting or native CAD acceptance.
