from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylFaceBuild import (
    CylFaceBuild,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylMateCtx import (
    CylMateCtx,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylPlace import (
    CylPlace,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylWrapFields import (
    CylWrapFields,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.GetCylExtent import (
    GetCylExtent,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.MakeCylFaceRef import (
    MakeCylFaceRef,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import (
    CompRefFields,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CopyPlacement import (
    CopyPlacement,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MakeMateChain import (
    MakeMateChain,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.SignedStamp import (
    SignedStamp,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireRecord,
)


# the active face wrapper updates only with its real component path and two independent placement caches
def MakeCylActive(
    Context: CylMateCtx,
    FaceValue: CylFaceBuild,
    PlaceValue: CylPlace,
    FileValue: ArchiveNode,
    SignedValue: bool,
) -> ArchiveNode:
    ChainValue = MakeMateChain(Context.StateValue.RootValue, PlaceValue.Occurrence)
    FieldsValue = PlaceValue.Occurrence.FieldsValue
    NumberValue = FieldInt(FieldsValue, "f3f8")
    Placement = RequireRecord(FieldsValue.get("f360"))
    ChildValue = Context.ChildValue
    Component = ArchiveNode(
        RuntimeClass("moCompFace_c", 1),
        {
            **CompRefFields(ChainValue),
            "f18": NumberValue,
            "f1c": NumberValue,
            "alias": 0,
            "fe8": MakeCylFaceRef(FaceValue, FileValue),
            "ff0": None,
        },
    )
    Values = CylWrapFields(Component, PlaceValue, FaceValue.RadiusValue)
    Lower, Upper = GetCylExtent(FaceValue, PlaceValue, SignedValue)
    Values.update(
        f08=SignedStamp(FieldInt(ChildValue.HeaderValue.FieldsValue, "f40")),
        f0c=FieldInt(ChildValue.CurrentConfig.FieldsValue, "f08"),
        has_f10=1,
        f10=CopyPlacement(Placement),
        has_f18=1,
        f18=CopyPlacement(Placement),
        f50=2,
        fb0=Lower,
        fb8=Upper,
        has_f108=1,
        f108=dict(zip("xyz", PlaceValue.LocalAxis, strict=True)),
    )
    return ArchiveNode(RuntimeClass("moCylinderRef_w", 1), Values)
