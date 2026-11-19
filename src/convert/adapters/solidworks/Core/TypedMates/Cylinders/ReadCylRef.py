from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
    RequireRecord,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CylChild import CylChild


# active surface references must resolve to the actual child feature and its first creation event
def ReadCylRef(Reference: ArchiveNode, ChildValue: CylChild) -> tuple[int, int]:
    KeeperValue = RequireRecord(Reference.FieldsValue.get("f10"))
    FeatureRef = RequireNode(KeeperValue.get("f10"), "moFR_c")
    ReferenceId = RequireRecord(FeatureRef.FieldsValue.get("f10"))
    Actual = (FieldInt(ReferenceId, "f00"), FieldInt(ReferenceId, "f08"))
    FeatureId = FieldInt(ChildValue.FeatureValue.FieldsValue, "f08")
    Expected = (
        FeatureId,
        DatumTime(ChildValue.LinkValue.ConfigValue.HeaderValue, FeatureId),
    )
    if Actual != Expected:
        raise ValueError(
            "concentric selected surface has a stale or foreign feature owner"
        )
    return Actual
