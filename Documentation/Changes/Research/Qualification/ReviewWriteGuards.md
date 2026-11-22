<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Validate scoped extrusion ends

The shared native-write guard now checks the extrusion inside `ScopedExtrude`.
It applies the existing primary-end, secondary-end, and missing-length checks before destination mutation.
Scope selection does not qualify an unresolved termination.

Public conversion and direct writers retain the same refusal for nested documents and suppressed history.
Explicit model serialization remains available for inspection.
Qualified blind scoped extrusions remain writable as interchange JSON.

## FreeCAD fixture migration

Existing FreeCAD integration fixtures must satisfy the required-feature and parameter-binding guards.
Supported fixtures need complete editable definitions and actual dimension parameters.
Unqualified native fixtures retain their format-level assertions and must verify public refusal separately.
The production guards remain enforced.

## Verification

The final Python 3.14 integration run passed 278 cases, with 10 existing skips for unavailable bundled FreeCAD examples.
The FreeCAD suite contributed 118 passing cases, including the 42 previously failing cases.
They cover file and stream preservation, nested documents, suppressed history, unknown ends, and qualified scoped controls.
Black, Ruff, focused Pyright, and documentation-link checks passed.
No CAD application ran, and these checks do not establish native conversion acceptance.

The [scoped-end gotcha](../../../Gotchas/Conversion/Qualification/ScopedExtrusionEnds.md) records the original bypass.
The semantic-marker change entry moved into this focused qualification directory to restore the parent directory's file-count limit.
