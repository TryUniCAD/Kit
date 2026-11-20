# Configuration unit tables inherit class slots

The first `moUnitsTable_c` in an ordinary part can declare its root class
and still need the parent archive's current counter. In the native ladder
part, its length override refers to class slot 10, which the table's
earlier length declaration allocates when the parent counter starts at
8. Starting at one leaves the class reference unresolved.

A later `moUnitsTable_c` can reuse class declarations from the first
table. Supply the caller's actual counter and inherited map entries.
The concave control's second table uses its earlier class slots at the
measured counter 60.
[Offsets, types and process evidence](../../../../../../re/solidworks/records/ConfigUnitTableSlice2026.md)
