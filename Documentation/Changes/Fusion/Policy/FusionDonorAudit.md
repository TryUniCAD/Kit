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

| Item                                     | Status                                                                                                 |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Drawing view body path                   | Fixed: ids come from the view source                                                                   |
| Drawing view source bytes and body key   | Fixed: source id and tail from the draft; body bits proven constant in 70 keys of 5 saves of 3 designs |
| Drawing view state mark                  | Fixed: proven constant after each body's bounds in 9 view states of 4 saves of 3 designs               |
| Drawing sheet defaults                   | Fixed: captured circle removed; per-class format values only                                           |
| Feature defaults                         | Fixed: schema type defaults only, with 73 earlier and 36 new cases accepted in Fusion                  |
| Drawing viewport size                    | Fixed: the viewport shows the whole paper                                                              |
| Drawing auto-created layout mark         | Fixed: removed                                                                                         |
| Drawing dimension text ratios            | Fixed: Arial glyph metrics from the font; 15 saved texts match to 4e-7 mm                              |
| Form stencil and shape tables            | Open                                                                                                   |
| Drawing ISO standard                     | Fixed: paper, borders, header and standard objects from rules; no save history                         |
| Drawing view shape flags                 | Fixed for axis base views and all projected views; slanted base views are refused                      |
| Drawing record numbering                 | Fixed: one counter per source and sheet, checked on a save with 5 sheets                               |
| Drawing dimensions and material families | Partly fixed: linear, aligned, vertical, radius, diameter and short layouts; materials fixed           |
| Form crease thresholds                   | Open                                                                                                   |

[Material families](../Materials/FusionMaterialFamilies.md) records the material fix.
The writer picks every family from the class and values it is given, using only schema vocabulary.
Nineteen held-out cases match Fusion's own documents in local Fusion.

## Limits

The audit covers the Fusion writers only.
Other adapters follow the same standard, and this entry does not audit them.
An item is fixed only when its captured data is gone from `src/` and local Fusion accepts held-out cases.

## Verification

The audit read each writer, each default table and each data file under `src/convert/formats/Fusion/`.
It traced each suspect value to the research script and control that produced it.
Static checks ran locally; no local automated tests were run.
