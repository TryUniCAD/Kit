# Fresh downstream reference construction sources

This source-only research addition binds actual fresh face/edge row allocation, component/entity ownership, embedded signed adjacent-face IDs and the initial coedge orientation in SOLIDWORKS 2026. It adds a metadata verifier and no production writer, codec registration or public capability.

The [construction record](../../../../../re/solidworks/records/DownstreamFreshReferenceAssignments2026.md) supplies field/call rules and explicit unresolved inputs. Its numeric ledger binds four original modules, 70 complete functions, 110 intervals, five delayed kernel imports and two runtime field registrations. [Actual source verification](../../../../../re/solidworks/measurements/2026/DownstreamFreshReferenceSource01.json) passed. Native runs, SDK executions, CAD inputs and held-out reads were zero.

The verifier takes `--bin-directory`, explicit `--kernel`, `--record` and an unused `--output`. It reads originals as bytes without loading vendor code. Use it to verify exact source custody. Native measurement remains open.

Three specific gotchas cover [construction scope](../../../../Gotchas/Conversion/Solidworks/Archive/Downstream/EntityReferencesNeedDownstreamConstructionScope.md), [duplicate role IDs](../../../../Gotchas/Conversion/Solidworks/Archive/Downstream/AdjacentFaceRoleMapsKeepDuplicateIds.md), and [primary-fin replacement](../../../../Gotchas/Conversion/Solidworks/Archive/Downstream/EdgePrimaryFinCanChangeBeforeReferenceCreation.md). Root owns further generated adjacency and native proof. Task `PR121-DownstreamFreshReferenceAssignments`, owner `configuration_header`, delivery PR #121.
