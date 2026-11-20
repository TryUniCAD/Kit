<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Scoped extrusion wrappers require end validation

## Expectation

Adding body-scope information preserves the public writer's extrusion termination checks.

## Actual behavior

The guard checked only direct `ExtrudeFeature` and `HoleFeature` definitions.
It skipped `ScopedExtrude`, including its enclosed extrusion.
Consequently, depthless through-all and native-only ends passed JSON export when wrapped, while identical direct definitions were refused.

## Repair

Inspect `ScopedExtrude.Extrusion` before applying the existing termination checks.
Keep the wrapper for serialization and body-scope validation.
Check primary ends, secondary ends, and missing lengths across nested and suppressed history.
Retain a qualified blind scoped control so the repair does not reject every wrapper.

See [the change entry](../../../Changes/Research/Qualification/ReviewWriteGuards.md).
