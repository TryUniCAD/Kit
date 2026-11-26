# Exact topology unit factors

## Behavior

The research graph comparator now constructs an exact rational length factor before deriving area and volume factors.
This preserves the declared decimal relationship between feet and millimetres when absolute tolerances are zero.
For example, one square foot equals `92903.04` square millimetres and one cubic foot equals `28316846.592` cubic millimetres.
The change preserves explicit unit declarations and existing tolerance choices.

## Usage and limits

Use the existing [bulk comparison command](../../../../Tasks/CompareDecodedDocuments.md) with each input's geometry unit.
No new option is required.
Exact scaling cannot recover precision already lost in source measurements or establish independent semantic or native acceptance.
See the [floating factor gotcha](../../../../Gotchas/Research/Comparison/FootTopologyFactorRounding.md).

## Verification

`tests/Research/Archives/Comparison/BulkUnitTests.py` exercises codec serialization and the real bulk command with equivalent feet/millimetre topology measurements at zero tolerance.
Separate cases retain genuine area-only and volume-only differences.
Scoped Black, Python steering, Pyright and syntax checks passed locally.
Local process tests were not run; remote shared-suite execution remains required.

Task `A06g-BulkDecodedComparison` remains owned by Codex and delivered in [PR #273](https://github.com/TryUniCAD/Kit/pull/273).
This correction does not qualify native pairs or conversion.
