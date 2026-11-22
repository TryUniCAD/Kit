<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# A supervised temporary root excludes its parent session

A fixture can expect the operating-system temporary root to contain its entire session.
The supervisor sets `TMPDIR` to the session's `work` directory.
On Windows, it also sets `TEMP` and `TMP` to that directory.
A temporary-root validator therefore rejects the parent session's job record and accepted input files.

Bind fixture session access to the exact `KIT_SESSION` value.
Require that session to be the canonical parent of the configured `work` directory.
Resolve input members within that bound session.
Keep generated work inside its `work` directory.
For a test that changes `TEMP`, place its settings and output under the selected temporary root.

The fixture transport and containment process checks exercise these boundaries.
See [the repair record](../../../Changes/Ci/Testing/FixtureMergeCi.md).
