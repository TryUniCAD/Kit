# Fusion history state identities

`HistoryState` now names the ASM journal values by their native meanings. The first two `history_stream` integers are the current state ID and the maximum allocated state ID. The fourth is the next entity tag. A bulletin board stores a status enum, not a board number.

## API and compatibility

| Previous field                     | Current field    | Meaning                                              |
| ---------------------------------- | ---------------- | ---------------------------------------------------- |
| `CurrentId`                        | `CurrentId`      | ID of the insertion delta state                      |
| `InitialId`                        | `InitialId`      | ID of the initial delta state                        |
| `Generation`                       | `CurrentStateId` | Current state of the owning history stream           |
| Implicit duplicate of `Generation` | `MaxStateId`     | Maximum allocated stream state ID                    |
| `Allocation`                       | `NextEntityTag`  | Next entity tag allocated by the history stream      |
| `BoardNumber`                      | `BoardStatus`    | `0` mainline, `1` stacked, `2` succeeded, `3` failed |

The first five positional arguments retain their order. The optional sixth argument, `MaxStateId`, defaults to the current state ID and is normalized in the immutable model. Existing keyword callers must use the corrected names. The corresponding `AuthorPolicy` names are `HistoryCurrentStateId`, `HistoryMaxStateId`, `HistoryNextEntityTag` and `HistoryBoardStatus`.

All state IDs and entity-tag counters are bounded nonnegative native signed 32-bit integers. The maximum state ID cannot be less than the current state ID. The qualified two-state profile still requires the insertion delta ID to follow the initial delta ID. The board status must be one of the four native enum values.

The canonical authored preamble remains `[4, 4, 0, 1, -1, 0, 1, -1]` and its board remains succeeded (`2`). Default cylinder, cuboid and frustum authoring therefore retains the same bytes. The third preamble integer is the native maximum retained-state setting; this profile keeps it zero. The profile also keeps its existing four reference values and rejects unsupported state layouts.

## Evidence

[Native evidence](../../../re/Fusion/Reconstruction/JournalStates/NativeEvidence.json) records symbol names, exact instruction ranges and the SHA-256 of the inspected ARM64 ASM 232 image. The compressed disassembly is included with its own digest. No native code was loaded or executed for this analysis.

`HISTORY_STREAM::save` at `0x62ca60` writes object offsets `0x90`, `0x94`, `0x78` and, when enabled by the native save option, `0x0`. The named current-state getter reads `0x90`. `note_state` increments `0x94`, then stores the new ID in both state fields. The native current-state setter permits rollback below that maximum. `tag` and `assign_tag` allocate entity tags from the saved `0x0` counter. `BULLETIN_BOARD::restore` reads an enum; its debug lookup supplies the four status names.

This refutes three earlier hypotheses: duplicated generation/size values, a fourth integer representing a stream identity or history-entry count, and a board ordinal. The native allocator evidence distinguishes entity tags from state IDs, operation IDs and body secondary identities.

[The read-only inventory](../../../re/Fusion/Reconstruction/JournalStates/Inventory.json) fully frames 69 distinct histories: 67 two-state and two three-state streams. The rolled-back archive stores current state `3` and maximum state `10`, with next entity tag `6`. Preserving the maximum avoids discarding allocation history during rollback.

## Verification and limits

Six added remote archive integration cases cover the rolled-back native journal, regenerated geometry with its distinct current/maximum metadata, three invalid board-status values and two invalid maximum-state values. Existing authored archive cases exercise the unchanged defaults. Black, Ruff, mypy, strict Pyright and repository steering checks passed the twelve changed or added production/integration modules. No local tests or production codec execution ran for this correction.

This change qualifies the corrected metadata in the existing complete two-state insertion journal. It does not add archived geometry, replacement/deletion bulletins, branching state trees, nonzero retention limits or the native `-1` entity-tag save-option variant. The Draft and offset-cylinder streams have three states and archived revisions; their fully framed research records are not a claim of complete semantic support. See the [state-counter gotcha](../../Gotchas/Conversion/Fusion/Geometry/FusionHistoryCounters.md).
