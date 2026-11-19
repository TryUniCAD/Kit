<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# SOLIDWORKS metadata does not prove feature availability

## Expectation

A type-library member, enum value or help topic can look like a complete list of
usable modelling controls.

## Observed boundary

The read-only installed snapshot reports executable `33.0.0.5050` and SldWorks
type library `33.0`. The curated planning taxonomy references official 2026 help.
A newer help topic does not prove the corresponding control exists in this older
installation. A declared command enum is a command candidate, not an observation
of an active toolbar button or successful command execution.

COM interfaces describe callable shapes. They do not establish selection marks,
feature-specific enum subsets, numeric ranges, units, defaults, licence state,
legal parameter combinations, UI availability, native record layouts or editable
translation. Optional add-ins and product tiers can introduce separate APIs and
licensing conditions. A retained obsolete interface also does not mean that it
is the preferred current authoring path.

## Workaround

Keep help version, executable version, type-library GUID/version and source hash
separate. Treat family-to-API name matches as discovery leads. Resolve each
feature through version-bound documentation and isolated controlled application
evidence before qualifying it. Record missing descriptors and unresolved types
as gaps; absence from the current snapshot is not universal nonexistence.

The [planner guide](../../Reference/Research/SolidworksPlannerCatalog.md) explains
how the saved database preserves these distinctions. The official
[CommandManager guide](https://help.solidworks.com/2026/english/SolidWorks/sldworks/c_commandmanager.htm)
describes context and add-in dependent controls, and the
[add-in toolbar guide](https://help.solidworks.com/2026/english/SolidWorks/sldworks/r_add_in_toolbars.htm)
describes installation prerequisites. No modelling command or CAD application
was launched to collect this declaration snapshot.
