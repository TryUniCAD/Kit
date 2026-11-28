from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# current part context confirmation cannot be generalized to drawing assembly or substituted archive owners
def RequirePartUi(GraphValue: ModelDefGraph) -> Mapping[str, object]:
    if (
        type(GraphValue) is not ModelDefGraph
        or type(CastValue(object, GraphValue.VersionValue)) is not int
        or GraphValue.VersionValue != 19000
        or GraphValue.DocumentValue.ClassValue != RuntimeClass("uiPartDoc_c", 1)
    ):
        raise ValueError("part ui requires an ordinary current part Definition")
    return GraphValue.DocumentValue.FieldsValue
