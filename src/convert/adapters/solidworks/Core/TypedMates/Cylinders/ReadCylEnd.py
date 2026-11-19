from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
)
from convert.adapters.solidworks.Assembly.PlanarMates.ReadChain import ReadChain
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarContext import PlanarContext
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlane import ReadVector
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CylChild import CylChild
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CylEndpoint import (
    CylEndpoint,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylRef import ReadCylRef
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylStamp import (
    ReadCylStamp,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CheckCylFrame import (
    CheckCylFrame,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CheckCylCaps import (
    CheckCylCaps,
)


# ordered selected faces must retain real registered wrappers and actual reciprocal occurrence chains
def ReadCylEnd(
    Context: PlanarContext,
    ChildValue: CylChild,
    Wrapper: ArchiveNode,
    MateId: int,
    OrderValue: int,
) -> CylEndpoint:
    FieldsValue = Wrapper.FieldsValue
    if (
        FieldInt(FieldsValue, "f74") != MateId
        or FieldInt(FieldsValue, "f7c") != OrderValue
        or not 0
        <= FieldInt(FieldsValue, "f78")
        < FieldInt(Context.ModelNode.FieldsValue, "fd48")
    ):
        raise ValueError("concentric resolved wrapper ownership or order differs")
    Component = RequireNode(FieldsValue.get("f58"), "moCompFace_c")
    if Component.FieldsValue.get("ff0") is not None:
        raise ValueError(
            "concentric active face has an unqualified secondary reference"
        )
    Occurrence = ReadChain(Context.ModelNode, Component)
    ItemValue = Context.OccurrenceMap[FieldInt(Occurrence.FieldsValue, "f08")]
    StampValue = ReadCylStamp(Context, ChildValue, ItemValue, Wrapper, Occurrence)
    Endpoint = CylEndpoint(
        ItemValue,
        ReadVector(FieldsValue.get("fd0")),
        ReadVector(FieldsValue.get("fe8")),
        ReadVector(FieldsValue.get("f108")),
        RequireScalar(FieldsValue.get("f100")),
        StampValue,
    )
    FaceValue = RequireNode(Component.FieldsValue.get("fe8"), "moFaceRef_c")
    SideValue = RequireNode(
        ReadRows(FaceValue.FieldsValue.get("f10"))[0].get("f08"),
        "moFromSktEntSurfIdRep_c",
    )
    _ = ReadCylRef(SideValue, ChildValue)
    if FieldInt(SideValue.FieldsValue, "f38") != ChildValue.ArcMarker:
        raise ValueError("concentric selected arc permanent marker differs")
    CheckCylCaps(ChildValue, FaceValue.FieldsValue)
    CheckCylFrame(Endpoint, ChildValue)
    return Endpoint
