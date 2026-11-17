from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetBuild import SheetBuild
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetZones import (
    MakeSheetZones,
)


# authored paper and scale inputs must compute the complete sheet own fields and actual support aliases
def MakeSheetOwn(
    BuildValue: SheetBuild, ProfileValue: ArchiveNode, DetailValue: ArchiveNode
) -> dict[str, object]:
    InputValue = BuildValue.InputValue
    Columns, RowCount, Horizontal, Vertical = MakeSheetZones(InputValue.LengthUnit)
    return {
        "f35c": 0,
        "f3f8": float(InputValue.NumeratorValue),
        "f400": float(InputValue.DenominatorValue),
        "f39c": 0,
        "f3c0": 13,
        "f3e8": 8.5 * 0.0254,
        "f3f0": 11 * 0.0254,
        "f3b8": "*.drt",
        "f3d0": InputValue.PropertyView,
        "f4a8": Horizontal,
        "f4b0": Horizontal,
        "f4b8": Vertical,
        "f4c0": Vertical,
        "f4c8": Columns,
        "f4cc": RowCount,
        "f4d8": 1,
        "has_f408": 1,
        "f408": ProfileValue,
        "has_f468": 0,
        "has_f418": 0,
        "f3b0": 0,
        "f420": 0,
        "f428": 0,
        "f3c8": None,
        "f438": ArchiveNode(RuntimeClass("suObList", 1), {"items": ()}),
        "has_f430": 0,
        "f390": DetailValue,
        "f448": 1,
        "has_f450": 0,
        "f3d8": 1,
        "f368_marker": 65535,
        "f474": 0,
        "f4d0": 0,
        "f4d4": 0,
        "f4e0": 1,
        "f4f0": 0,
        "n_ink_views": 0,
        "ink_views": (),
    }
