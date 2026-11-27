from pathlib import PureWindowsPath

from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import (
    ReadChildStamp,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    RequireNode,
    RequireRecord,
)
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarContext import PlanarContext
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarEndpoint import (
    PlanarEndpoint,
)
from convert.adapters.solidworks.Assembly.PlanarMates.ReadChain import ReadChain
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlane import (
    ReadPlane,
    ReadVector,
)


# the typed occurrence and synchronized child provide the public plane identity
def ReadEndpoint(
    Context: PlanarContext,
    WrapperValue: object,
    MateId: int,
    OrderValue: int,
    *,
    Deferred: bool = False,
) -> PlanarEndpoint:
    Wrapper = RequireNode(WrapperValue, "moPlaneRef_w")
    NextWrapperId = FieldInt(Context.ModelNode.FieldsValue, "fd48")
    Plane = ReadPlane(Wrapper, MateId, OrderValue, NextWrapperId)
    Occurrence = ReadChain(Context.ModelNode, Plane)
    FeatureId = FieldInt(Occurrence.FieldsValue, "f08")
    ItemValue = Context.OccurrenceMap.get(FeatureId)
    if ItemValue is None or ItemValue.suppressed or ItemValue.virtual:
        raise ValueError(
            "the resolved occurrence is missing from the enabled root index"
        )
    Definition = Context.DefinitionMap.get(ItemValue.definition_id)
    if Definition is None or Definition.document_type != "PART":
        raise ValueError("the resolved occurrence has no explicit part definition")
    SourceName = PureWindowsPath(Definition.source_path).name.casefold()
    ChildValue = Context.ChildMap.get((SourceName, ItemValue.configuration_id))
    DatumId = FieldInt(RequireRecord(Plane.FieldsValue.get("ff0")), "f00")
    if Deferred:
        Stamp = FieldInt(Wrapper.FieldsValue, "f08") & 0xFFFFFFFF
        if (
            FieldInt(Wrapper.FieldsValue, "f0c") != ItemValue.configuration_id
            or FieldInt(Occurrence.FieldsValue, "f3e0") != Stamp
        ):
            raise ValueError("deferred mate wrapper differs from its occurrence")
        return PlanarEndpoint(
            FeatureId,
            ItemValue.object_id,
            ItemValue.definition_id,
            ItemValue.configuration_id,
            Stamp,
            DatumId,
            "",
            ReadVector(Wrapper.FieldsValue.get("fd0")),
            ReadVector(Wrapper.FieldsValue.get("fe8")),
        )
    if ChildValue is None:
        raise ValueError("the resolved occurrence has no explicit part configuration")
    Stamp = ReadChildStamp(
        Wrapper,
        Occurrence,
        ChildValue,
        ItemValue.configuration_id,
        ItemValue.configuration_name,
        SourceName,
    )
    Datum = RequireNode(ChildValue.DatumNodes.get(DatumId), "moRefPlane_c")
    if FieldInt(Datum.FieldsValue, "f08") != DatumId:
        raise ValueError("the real child datum identity differs")
    return PlanarEndpoint(
        FeatureId,
        ItemValue.object_id,
        ItemValue.definition_id,
        ItemValue.configuration_id,
        Stamp,
        DatumId,
        ReadNodeName(Datum),
        ReadVector(Wrapper.FieldsValue.get("fd0")),
        ReadVector(Wrapper.FieldsValue.get("fe8")),
    )
