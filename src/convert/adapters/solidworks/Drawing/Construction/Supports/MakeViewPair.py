from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Geometry.IdentityXform import (
    IdentityXform,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Drawing.Construction.Sheet.MakeSheetPlane import (
    MakeSheetPlane,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.MakeSheetRef import (
    MakeSheetRef,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.MakeSheetSketch import (
    MakeSheetSketch,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetBuild import SheetBuild
from convert.adapters.solidworks.Drawing.Construction.Supports.RegisterDrawMut import (
    RegisterDrawMut,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptNode,
    NeedDrawNumber,
)


# each view sketch pair reuses the proved empty drawing constructors with its own sheet or model coordinate frame and actual drawing owner
def MakeViewPair(
    ViewValue: ArchiveNode,
    DrawingValue: ArchiveNode,
    BuildValue: SheetBuild,
    OriginValue: dict[str, object],
    FrameValue: dict[str, object],
    Allocator: PersistentIds,
    AxesValue: tuple[tuple[float, ...], ...] | None,
) -> tuple[ArchiveNode, ArchiveNode]:
    PlaneValue = MakeSheetPlane(ViewValue, BuildValue)
    DataValue = dict(
        NeedConceptNode(
            PlaneValue.FieldsValue["f6f8"], "moAbsoluteRefPlnData_c"
        ).FieldsValue
    )
    DataValue.update({"root": dict(OriginValue), "f20": FrameValue})
    if AxesValue is None:
        DataValue.update(
            {"b0": 0.0, "b1": 0.0, "b2": 0.0, "b3": 0.0, "f88": IdentityXform()}
        )
        PlaneValue.FieldsValue["f6f8"] = ArchiveNode(
            RuntimeClass("moDrawingRefPlnData_c", 1), DataValue
        )
    else:
        AxisU, AxisV, Normal = AxesValue
        DataValue["normal"] = dict(zip("xyz", Normal, strict=True))
        PlaneValue.FieldsValue["f6c0"] = {
            NameValue: NeedDrawNumber(OriginValue[NameValue])
            + NeedDrawNumber(DataValue["b1"]) * UValue
            + NeedDrawNumber(DataValue["b2"]) * VValue
            for NameValue, UValue, VValue in zip("xyz", AxisU, AxisV, strict=True)
        }
        PlaneValue.FieldsValue["f6f8"] = ArchiveNode(
            RuntimeClass("moAbsoluteRefPlnData_c", 1), DataValue
        )
    Reference = MakeSheetRef(PlaneValue, DrawingValue, BuildValue.ArchiveVersion)
    _ = Allocator.AllocateMut(PlaneValue)
    ProfileBuild = ReplaceValue(BuildValue, FirstIdValue=Allocator.NextValue - 2)
    ProfileValue = MakeSheetSketch(ViewValue, Reference, ProfileBuild)
    RegisterDrawMut(ProfileValue, Allocator)
    ProfileValue.FieldsValue["pd_ff0"] = FrameValue
    PlaneValue.FieldsValue["f0c"] = 0
    ProfileValue.FieldsValue["f0c"] = 0
    if (
        NeedConceptNode(Reference.FieldsValue["f58"], "moUnitComponent_c").FieldsValue[
            "owner"
        ]
        is not DrawingValue
    ):
        raise ValueError("drawing view support reference lost its actual model owner")
    return PlaneValue, ProfileValue
