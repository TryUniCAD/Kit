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
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.MakeCylFacet import (
    MakeCylFacet,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.MakeAtomFeat import (
    MakeAtomFeat,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import (
    CompRefFields,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CopyPlacement import (
    CopyPlacement,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.SignedStamp import (
    SignedStamp,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    RequireNode,
    RequireRecord,
)


# the independent support snapshot belongs to the parent and retains its own faceted cylinder
def MakeCylSupport(
    Context: CylMateCtx, FaceValue: CylFaceBuild, PlaceValue: CylPlace
) -> ArchiveNode:
    Parent = Context.StateValue.RootValue
    Header = Context.HeadersValue[0]
    RootValue = RequireNode(Parent.FieldsValue.get("f990"), "moUnitComponent_c")
    Geometry = MakeAtomFeat(Parent, Context.InputValue.TargetValue).FieldsValue
    Geometry.update(
        f6c0=dict.fromkeys("xyz", 0.0),
        f6dc=4,
        f6e0=0,
        f6e8=None,
        f6f0=0,
        f6f8=dict(zip("xyz", PlaceValue.OriginValue, strict=True)),
        f710=dict(zip("xyz", PlaceValue.WorldAxis, strict=True)),
        f728=FaceValue.RadiusValue,
    )
    Component = ArchiveNode(
        RuntimeClass("moCompRefCylinder_c", 1),
        {
            **CompRefFields(RootValue),
            "ff0": {"f00": -1, "f08": DatumTime(Header, -1)},
            "ff8": ArchiveNode(RuntimeClass("moRefCylinder_c", 1), Geometry),
            "f90": FaceValue.BodyAtom,
            "f94": FaceValue.FaceNodeId,
            "has_fb0": 1,
            "fb0": MakeCylFacet(FaceValue),
            "has_fb8": 1,
            "fb8": ReadNodeName(PlaceValue.Occurrence) + "@" + ReadNodeName(Parent),
            "has_fc8": 1,
            "fc8": CopyPlacement(
                RequireRecord(PlaceValue.Occurrence.FieldsValue.get("f360"))
            ),
        },
    )
    Values = CylWrapFields(Component, PlaceValue, FaceValue.RadiusValue)
    Values.update(
        f08=SignedStamp(FieldInt(Header.FieldsValue, "f40")),
        f0c=FieldInt(Context.StateValue.CurrentConfig.FieldsValue, "f08"),
    )
    return ArchiveNode(RuntimeClass("moCylinderRef_w", 1), Values)
