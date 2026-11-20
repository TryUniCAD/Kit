# A saved stock chooser may lack its wrapper face carrier

The disclosed original stores a `moFaceRef_c` in the selected wrapper's `ff0` field. SOLIDWORKS also saved the rebuilt two-stock derivative with a null `ff0` and zero `f100` and `f104`. Its actual consumed atom, self-component and both cut chooser arrays remain present.

Use the three saved atoms, actual consumed-stock selector and linked chooser records together. The operation's `f4a8` and `f4c0` face rows are separate objects. Corresponding constituent representations and their feature references share object identity. Every face combines two stock sides, both caps and one circular cut reference under the selected chooser's actual external owner. Match stock and circle markers to their linked profiles.

The two provisional cold atoms cannot satisfy the same checks. A copied matching map index, a different valid mapped representation, a crossed producer, or a changed arc marker each produces a refusal.

[Typed selector receipt](../../../../../../re/solidworks/measurements/2026/TwoStockSavedSelector01.json) ·
[Original saved ownership](../../../../../../re/solidworks/records/ThroughAllMultiStockArchive2026.md)
