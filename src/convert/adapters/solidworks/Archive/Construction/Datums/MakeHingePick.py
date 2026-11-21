from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Construction.Origin.MakeOriginRef import (
    MakeOriginRef,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
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
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
    RequireRecord,
)


# each wrapper snapshots the actual modeled support and its independently registered creation
def MakeHingePick(
    SystemValue: PartSystem,
    DatumValue: ArchiveNode,
    AxisValue: str,
    Headers: tuple[ArchiveNode, ...],
) -> ArchiveNode:
    Reference = MakeOriginRef(DatumValue, SystemValue.RootValue, AxisValue)
    NativeId = FieldInt(DatumValue.FieldsValue, "f08")
    CreatedAt = DatumTime(Headers[0], NativeId)
    if DatumTime(Headers[1], NativeId) != CreatedAt:
        raise ValueError("hinge support creation differs between its own headers")
    Identity = RequireRecord(Reference.FieldsValue["ff0"])
    Reference.FieldsValue["ff0"] = {**Identity, "f08": CreatedAt}
    Source = RequireNode(
        DatumValue.FieldsValue["f6f8"], "moDefaultRefPlnData_c"
    ).FieldsValue
    Transform = RequireRecord(Source["f20"])
    Fields = WrapperFields(Reference)
    Fields.update(
        f68=1,
        f08=SignedStamp(FieldInt(Headers[0].FieldsValue, "f40")),
        f0c=FieldInt(SystemValue.ConfigValues[0].FieldsValue, "f08"),
        fd0=dict(RequireRecord(Source["root"])),
        fe8=dict(RequireRecord(Source["normal"])),
        f100={**Transform, "f08": dict(RequireRecord(Transform["f08"]))},
        f188=MakePoint(),
    )
    Fields.update(
        {
            KeyValue: Source[f"b{Index}"]
            for Index, KeyValue in enumerate(("fb0", "fb8", "fc0", "fc8"))
        }
    )
    return ArchiveNode(RuntimeClass("moPlaneRef_w", 1), Fields)
