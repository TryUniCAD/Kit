from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import (
    KeywordDim,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import (
    KeywordFeature,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)


# shell keywords refer to the same live driver and persistent shell feature as the resolved graph
def MakeShellKey(Feature: ArchiveNode, Driver: DimensionGraph) -> KeywordFeature:
    Parameter = Driver.ParameterValue
    Thickness = RequireScalar(Parameter.FieldsValue["f58"])
    return KeywordFeature(
        FieldInt(Feature.FieldsValue, "f08"),
        ReadNodeName(Feature),
        "Shell",
        "Feature",
        (KeywordDim(ReadNodeName(Parameter), Thickness * 1000, None),),
        (),
        None,
        None,
    )
