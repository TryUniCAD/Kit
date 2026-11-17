from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Drawing.Construction.Sheet.AtomZeros import KAtomZeros
from convert.adapters.solidworks.Drawing.Construction.Sheet.MakeDrawFeature import (
    MakeDrawFeature,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.ScaleFrame import (
    MakeScaleFrame,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetBuild import SheetBuild


# the profile handle must observe the native absolute plane before its persistent identifier is assigned
def MakeSheetPlane(SheetValue: ArchiveNode, BuildValue: SheetBuild) -> ArchiveNode:
    PlaneValue = MakeDrawFeature(
        "moRefPlane_c", BuildValue.NamesValue.PlaneName, SheetValue, -1, BuildValue
    )
    PlaneValue.FieldsValue.update({FieldName: 0 for FieldName in KAtomZeros})
    PlaneValue.FieldsValue.update(
        {
            FieldName: ()
            for FieldName in ("f498", "f678", "f5d8", "f400", "f3e0", "f610", "f620")
        }
    )
    PlaneValue.FieldsValue.update(
        {
            "f35c": 0,
            "f368": {"n": 0, "items": ()},
            "f388": {"n": 0, "items": ()},
            "f538": None,
            "f4a0": 1,
            "f6c0": {"x": 0.0, "y": 0.0, "z": 0.0},
            "f6dc": 4,
            "f6e0": 0,
            "f6e8": None,
            "f6f0": 0,
            "f6f8": ArchiveNode(
                RuntimeClass("moAbsoluteRefPlnData_c", 1),
                {
                    "root": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "normal": {"x": 0.0, "y": 0.0, "z": 1.0},
                    "f20": MakeScaleFrame(
                        1.0
                        / (
                            BuildValue.InputValue.NumeratorValue
                            / BuildValue.InputValue.DenominatorValue
                        )
                    ),
                    "b0": 0.1618 * 0.5,
                    "b1": -0.1618 * 0.5,
                    "b2": 0.1 * 0.5,
                    "b3": -0.1 * 0.5,
                    "f48": None,
                    "f50": 0,
                    "f54": 1,
                    "f58": 2,
                    "old_e5": 0,
                    "f5c": 1,
                    "f60": 0,
                    "f64": 0,
                    "f68": None,
                    "f70": None,
                    "f78": None,
                },
            ),
        }
    )
    return PlaneValue
