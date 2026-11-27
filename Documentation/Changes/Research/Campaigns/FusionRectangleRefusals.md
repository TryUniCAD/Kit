<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Remaining Fusion rectangle refusals

The [investigation](../../../../re/Fusion/Notes/RectangleRefusals.md) partitions the
72 remaining ladder refusals after PR #265's bounded reader improvement.
It records exact source revisions, the first rejecting guard, later frame and
signed-volume boundaries, native measurement comparisons, and reproduction.

## Verification

A fresh public SDK replay at `14259fb00f2f54ef2501c4a9afd596318f16c676`
reproduced all 144 hash-bound outcomes: 72 strict successes and 72 refusals.
All typed native states parsed. Six public CLI probes reproduced the six
placement/direction groups. The 72 refused solids' journal and snapshot vertices
matched the native frame derivation exactly; derived volume, area and centroid
agreed with recorded native measurements.

## Limits

This documentation changes no reader or writer behavior. It qualifies no new
placement, complete semantic recovery, target conversion or editable native
output. Separate held-out controls remain necessary for the proposed extension.
The evidence remains bound to the inspected PR revision, independent of later
changes to main. No fresh vendor application measurements were performed.
