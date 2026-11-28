from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import (
    KeywordFeature,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    RequireNode,
)


# part keyword axes must retain the registered axis feature and its indexed name
def AxisKeyRow(NodeValue: ArchiveNode) -> KeywordFeature:
    AxisValue = RequireNode(NodeValue, "moRefAxis_c")
    return KeywordFeature(
        FieldInt(AxisValue.FieldsValue, "f08"),
        ReadNodeName(AxisValue),
        "Axis",
        "Feature",
        (),
        (),
        None,
        None,
    )
