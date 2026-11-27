<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Cyclic loop neighborhoods can mispair distinct lines

## Expectation

A comparison of an unchanged rectangle across positive and negative extrusion variants should match each line to the line with the same physical coordinates, while retaining source loop-order and extrusion differences.

## Observed behavior

The saved P03 controls start the selected profile loop at different edges. The research matcher's neighborhood-first preference rotated four physically distinct lines onto different coordinates and introduced false coordinate differences and axis-relation ambiguity. Native geometry and ordered profile references provide separate observations; loop indexing must not outweigh uniquely equal line fields.

## Resolution

The matcher prioritizes mutually unique candidates with no field differences before neighborhood preference. Such a pair is forced in every field-preserving residual bijection. Multiple equal candidates retain ambiguity. The original loop records remain ordered and expose all eight indexed-reference differences, while depth and body bounds retain their actual sign changes.

The [change entry](../../../Changes/Research/Readers/Comparison/NativeDirectionMatching.md) links the scope and actual process evidence. This correction does not establish independent semantic qualification or native acceptance.
