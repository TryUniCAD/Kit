# Thin wall thickness follows live display owners

The thin specification contains two inline doubles at `f30` and `f38`.
The exact SOLIDWORKS 2026 SP05.2 live wall getters follow the display
references at `f08` and `f10` and call the display's value virtual.
The named end-thickness getter uses `f30`. The ordinary thin revolve
constructor allocates distinct distance displays before attaching the
thin spec to the feature.

Follow each actual display through its dimension to the live parameter.
Use a source that changes one wall driver at a time. The constructor
can allocate two displays even when the authored wall mode has one
editable control. The final save determines which owners persist.

[Pointer and field evidence](../../../../../../re/solidworks/records/RevolveFamilySources2026.md)
