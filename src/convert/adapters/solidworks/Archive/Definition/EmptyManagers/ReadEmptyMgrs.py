from convert.adapters.solidworks.Archive.Definition.EmptyManagers.EmptyMgrInput import (
    EmptyMgrInput,
)
from convert.adapters.solidworks.Archive.Definition.EmptyManagers.NeedEmptyBom import (
    NeedEmptyBom,
)
from convert.adapters.solidworks.Archive.Definition.EmptyManagers.ReadEmptyAppr import (
    ReadEmptyAppr,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the ordinary part profile keeps manager presence separate from every unrelated ui scalar
def ReadEmptyMgrs(GraphValue: ModelDefGraph) -> EmptyMgrInput:
    if (
        type(GraphValue) is not ModelDefGraph
        or GraphValue.VersionValue != 19000
        or GraphValue.DocumentValue.ClassValue != RuntimeClass("uiPartDoc_c", 1)
    ):
        raise ValueError(
            "empty model managers require a current ordinary part Definition"
        )
    FieldsValue = GraphValue.DocumentValue.FieldsValue
    if "fab8" not in FieldsValue:
        raise ValueError("empty model manager state lacks its actual BOM pointer")
    BomValue = FieldsValue["fab8"]
    if BomValue is not None:
        NeedEmptyBom(BomValue)
    return EmptyMgrInput(BomValue is not None, ReadEmptyAppr(FieldsValue))
