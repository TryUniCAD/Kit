# A reader alias does not enable the corresponding writer

## Expectation

Selecting `solidworks.sldasm` in discovery might appear to enable assembly output.

## Actual behavior

The primary SOLIDWORKS entry reads parts and assemblies but writes bounded parts only.
At base `1619f00bf532caad262d1557bd69281179e5c497`, JSON exposed this difference but text output omitted aliases.
This is registry metadata, not native acceptance evidence.

## Workaround

Use `kit formats solidworks.sldasm --json` and inspect `write_extensions` and `write_aliases`.
The focused lookup and text alias columns expose the existing direction limits.
Follow [format selection](../../Tasks/SelectFormat.md) before conversion.
The [change record](../../Changes/Commands/FocusedFormatDiscovery.md) identifies process coverage and verification limits.
