<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# SOLIDWORKS planner capability catalogue

## Change

Research planners can inspect SOLIDWORKS feature families, subfeatures and the
installed API declaration surface in the same SQLite/CSV inventory format as
[Fusion PR #163](https://github.com/TryUniCAD/Kit/pull/163).

The curated plan contains 68 families and 585 subfeatures with option research
axes, dependencies, nine delivery waves, acceptance gates and official source
URLs. The installed metadata snapshot covers 31 type libraries, 3,282 types,
28,087 function/accessor declarations, 43,084 parameters and 15,284 variables.
These are metadata counts, not qualified feature counts. The executable reports
`33.0.0.5050`; the core SldWorks type library reports `33.0`. The plan's official
help baseline is 2026, so cross-version availability remains an explicit gap.

The bundle records sources, items, relationships and gaps, exports readable CSVs,
and includes a verifier for hashes, SQLite integrity, foreign keys, canonical
content and export counts. Read the
[collection and query guide](../../Reference/Research/SolidworksPlannerCatalog.md)
for commands and interpretation. The
[metadata availability gotcha](../../Gotchas/Research/SolidworksMetadataAvailability.md)
explains why declarations and command enums cannot qualify authorability.

## Ownership and exit condition

| Field          | Record                                                                                                                           |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Task           | `SW-CATALOG`                                                                                                                     |
| Owner          | Current catalogue PR coordinator                                                                                                 |
| Scope          | Installed declaration inventory and explicit feature planning taxonomy                                                           |
| Research lanes | API inventory; catalogue/database verification; feature plan and documentation                                                   |
| Dependencies   | A03/A07/A08/A09/A10 programme boundaries in PR #158; planner integration in PR #162                                              |
| Delivery       | [PR #164](https://github.com/TryUniCAD/Kit/pull/164), branch `codex/solidworks-planner-catalog`; PR #163 is the format reference |
| Exit           | Source-bound saved inventory, independently verified deterministic bundle, documented gaps and scoped PR review                  |

The catalogue supplies research inputs. It does not implement scheduler execution,
transfer programme ownership, change campaign ledgers or promote any existing
bounded alpha evidence. Every authoring, decoding, writing and verification field
remains `unverified`.

## Verification boundary

Fresh-process extraction reproduced the metadata, and an independent descriptor
audit matched every declared type, member, parameter and variable. Actual saved
inputs rebuilt successfully; the independent verifier passed SQLite integrity,
foreign keys, canonical records and every CSV field. Five process integration
cases passed with pytest 9.1.1: deterministic regeneration/readback, altered-export
rejection, manifest-version tamper rejection, rehashed-view tamper rejection and
existing-destination preservation.
Black, Prettier and focused steering checks passed. The saved database contains
94,299 items, 5,345 relations,
60 sources and 5,239 explicit gaps.

The installed read-only extraction completed with zero recorded descriptor or
library errors. The curated JSON has unique family/subfeature identities,
resolvable dependencies and explicit acceptance gates. Bundle verification is
recorded against its actual manifest and PR revision; this page does not claim
unexecuted merge-group acceptance, native application acceptance or complete
SOLIDWORKS translation support.
