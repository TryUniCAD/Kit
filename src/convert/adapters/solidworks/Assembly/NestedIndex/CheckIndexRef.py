from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Construction.Geometry.ReadRigidXform import (
    ReadRigidXform,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.Assembly import NativeAsmItem
from convert.adapters.solidworks.Assembly.NestedIndex.IndexModel import IndexModel
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    FieldText,
    ReadNodeName,
    RequireNode,
    RequireRecord,
)


# index placements need reciprocal feature identity and exact child ownership before publishing the local order
def CheckIndexRef(
    ItemValue: NativeAsmItem,
    Reference: ArchiveNode,
    Target: IndexModel,
) -> None:
    Fields = Reference.FieldsValue
    Feature = RequireNode(Fields.get("f4f8"), "moExtFeature_c")
    TargetFile = RequireNode(Fields.get("f3b0"), "moExtObject_c")
    Selection = RequireRecord(Fields.get("f3c0"))
    if (
        Feature.FieldsValue.get("f50") is not Reference
        or FieldInt(Feature.FieldsValue, "f44") != ItemValue.feature_id
        or ReadNodeName(Reference) != f"{ItemValue.name}-{ItemValue.reference_number}"
        or ReadFileKey(TargetFile) != Target.KeyValue
        or FieldInt(Selection, "f10") != ItemValue.configuration_id
        or FieldText(Selection, "f08") != ItemValue.configuration_name
    ):
        raise ValueError("nested index occurrence differs from its physical owner")
    Matrix, Origin = ReadRigidXform(RequireRecord(Fields.get("f360")))
    PoseValue = (*Matrix[:3], 0.0, *Matrix[3:6], 0.0, *Matrix[6:], 0.0, *Origin, 1.0)
    if any(
        not IsClose(Actual, Expected, rel_tol=1e-14, abs_tol=1e-16)
        for Actual, Expected in zip(ItemValue.transform, PoseValue, strict=True)
    ):
        raise ValueError("nested index placement differs from its physical owner")
