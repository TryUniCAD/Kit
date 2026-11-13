# Donor data audit and ban for Fusion writers

## Behavior

The [donor data ban](../../../Reference/Research/FusionDonorBan.md) states how the [no donor blocks standard](../../../../.agents/skills/standard-pr-practice/references/Standards/Portable/NoDonorBlocks.md) applies to the Fusion codecs.
It defines donor files, donor blocks, case-specific values and per-case tables with Fusion examples.
It lists what is banned in `src/` and in output, what is allowed, and the limits of the `re/` exemption.
It gives a procedure to replace donor data with black-box experiments and a review checklist.

Seven gotchas under [Donors](../../../Gotchas/Conversion/Fusion/Donors/) record the traps that let donor data look like format knowledge:

- [An id that matches every control can belong to one design](../../../Gotchas/Conversion/Fusion/Donors/FusionSingleDesignIds.md)
- [A filter for values equal across controls keeps design geometry](../../../Gotchas/Conversion/Fusion/Donors/FusionEqualValueFilter.md)
- [First-instance feature defaults carry values from one control](../../../Gotchas/Conversion/Fusion/Donors/FusionFirstInstanceDefaults.md)
- [A table keyed by a layout hash does not scale](../../../Gotchas/Conversion/Fusion/Donors/FusionLayoutHashKeys.md)
- [A saved viewport size is window state, not a sheet property](../../../Gotchas/Conversion/Fusion/Donors/FusionSavedWindowState.md)
- [Text metrics fitted from one string fail for other text](../../../Gotchas/Conversion/Fusion/Donors/FusionOneGlyphMetrics.md)
- [A template drawing is a donor file](../../../Gotchas/Conversion/Fusion/Donors/FusionTemplateDrawings.md)

The [term register](../../../Standards/Terminology.md) defines the new terms, and [AGENTS.md](../../../../AGENTS.md) states the ban for every agent.

## Audit

A review of every writer under `src/convert/formats/Fusion/` at commit `1a3b554d0` found 15 items.
Fourteen items are donor or case-specific data, and the [donor data ban](../../../Reference/Research/FusionDonorBan.md#audit-of-the-fusion-writers) lists them with their general rules.
The fifteenth item is an input guard in `Assembly/Solids/SnapshotScope.py`.
It checks a fixed 12-byte prefix of a 96-byte workbook before an edit and refuses other layouts.
It reads input and writes no vendor bytes, so it is not donor data.

| Item                                     | Status                                                                                |
| ---------------------------------------- | ------------------------------------------------------------------------------------- |
| Drawing view body path                   | Open                                                                                  |
| Drawing view source bytes and body key   | Open                                                                                  |
| Drawing view state mark                  | Open                                                                                  |
| Drawing sheet defaults                   | Open                                                                                  |
| Feature defaults                         | Fixed: schema type defaults only, with 73 earlier and 36 new cases accepted in Fusion |
| Drawing viewport size                    | Open                                                                                  |
| Drawing auto-created layout mark         | Open                                                                                  |
| Drawing dimension text ratios            | Open                                                                                  |
| Form stencil and shape tables            | Open                                                                                  |
| Drawing ISO standard                     | Open                                                                                  |
| Drawing view shape flags                 | Open                                                                                  |
| Drawing record numbering                 | Open                                                                                  |
| Drawing dimensions and material families | Open                                                                                  |
| Form crease thresholds                   | Open                                                                                  |

## Limits

The audit covers the Fusion writers only.
Other adapters follow the same standard, and this entry does not audit them.
An item is fixed only when its captured data is gone from `src/` and local Fusion accepts held-out cases.

## Verification

The audit read each writer, each default table and each data file under `src/convert/formats/Fusion/`.
It traced each suspect value to the research script and control that produced it.
Static checks ran locally; no local automated tests were run.
