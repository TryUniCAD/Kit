# Native saved edits change ASM integer width and topology tags

## Expectation

A saved parameter edit keeps the original eight-byte prism history layout and empty topology entity tags.

## Actual behavior

Fusion 2706.1.17 saved the independently edited P03 controls with `ASM BinaryFile4` headers. The history retained nonnegative entity identities on geometric records. Treating those fields as fixed `-1` values rejected valid source history. The auxiliary snapshot can also use four-byte integers.

## Workaround

Read the width from the ASM signature. Pass it to every integer-bearing record reader. Preserve topology identities as typed source values, separate from the body key. Re-emit the original width through the typed journal and snapshot serializers.

The [retained controls and native measurements](../../../../../../re/Fusion/Reconstruction/NativeEditedPrisms/Findings.md) establish this behavior. [The reader change](../../../../../Changes/Fusion/Reading/FusionSavedPrismEdits.md) records its scope and verification.
