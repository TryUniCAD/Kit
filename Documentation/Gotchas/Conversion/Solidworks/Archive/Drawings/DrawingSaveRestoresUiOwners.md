# Drawing save reconstructs selected UI owners

In the disclosed reduced native drawing, the viewport, drawing environment
and BOM manager can be absent on input. On save after a sheet scale edit,
SOLIDWORKS writes them again. Empty line style and font tables in the same
Definition remain empty.

Validate each owner independently and inspect the saved derivative when
qualifying a neutral drawing cache state. The combined omission completed
clean native open, rebuild, save and fresh reopen.
[Matched-path native result](../../../../../../re/solidworks/measurements/2026/DrawingBlankUiOmission01.json)
