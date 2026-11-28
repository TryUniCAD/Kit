from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    DatumPoint,
    KDatumVector,
    KHingeAxis,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import (
    CompRefFields,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.SignedStamp import (
    SignedStamp,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.WrapperFields import (
    WrapperFields,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# the coincidence line binds the actual hinge its paired creation record and the active configuration
def MakeAngleLine(
    SystemValue: PartSystem,
    HingeValue: ArchiveNode,
    HeaderValue: ArchiveNode,
    Endpoints: tuple[KDatumVector, KDatumVector],
    CreatedAt: int,
) -> ArchiveNode:
    SelfValue = ArchiveNode.RequireNode(SystemValue.RootValue.FieldsValue["f990"])
    Fields = CompRefFields(SelfValue)
    Fields.update(
        ff0={"f00": FieldInt(HingeValue.FieldsValue, "f08"), "f08": CreatedAt}, ff8=None
    )
    Reference = ArchiveNode(RuntimeClass("moCompRefAxis_c", 1), Fields)
    First, Second = Endpoints
    Wrapper = WrapperFields(Reference, AxisSupport=True)
    Wrapper.update(
        f68=1,
        f08=SignedStamp(FieldInt(HeaderValue.FieldsValue, "f40")),
        f0c=FieldInt(SystemValue.ConfigValues[0].FieldsValue, "f08"),
        fb0=0.0,
        fb8=First[2] - Second[2],
        fc8=DatumPoint(First),
        fe0=DatumPoint(KHingeAxis),
        ff8=0,
    )
    return ArchiveNode(RuntimeClass("moLineRef_w", 1), Wrapper)
