from dataclasses import dataclass as DataClass, replace as ReplaceData
from convert.adapters.solidworks.Config.RootRules import (
    KAtomRules,
    KMaterialRules,
    KPrefixRules,
)
from convert.adapters.solidworks.Container.Archive import LayoutTable

# the root seed and inline fields have been independently checked for this generation
KConfigGen = 19000

# native configuration archives enter through the same registered part class
KRootClass = "moPart_c"


# staged layout scopes prevent early wildcard children from seeing later definitions
@DataClass(frozen=True, slots=True)
class PartLayouts:
    Prefix: LayoutTable
    Material: LayoutTable
    Atoms: LayoutTable


# exact readback comparison must resolve the existing format grammar without runtime file reads
def LoadPartLayouts() -> PartLayouts:
    return PartLayouts(
        LayoutTable.FromMapping({"classes": KPrefixRules}),
        LayoutTable.FromMapping({"classes": KMaterialRules}),
        LayoutTable.FromMapping({"classes": KAtomRules}),
    )


# each new root child gets its preceding scalar width from actual archive framing
def ExtendRoot(
    Layouts: LayoutTable,
    OtherLayouts: LayoutTable,
    Slots: tuple[str, ...],
    Widths: tuple[int, ...],
) -> LayoutTable:
    RootLayout = Layouts[KRootClass]
    Entries = {**Layouts.classes, **OtherLayouts.classes}
    StartSlot = len(RootLayout.child_slots) - 1
    RunWidths = {
        **RootLayout.runs,
        **{str(SlotIndex): Width for SlotIndex, Width in enumerate(Widths, StartSlot)},
    }
    Entries[KRootClass] = ReplaceData(
        RootLayout, child_slots=RootLayout.child_slots + Slots, runs=RunWidths
    )
    return ReplaceData(Layouts, classes=Entries)
