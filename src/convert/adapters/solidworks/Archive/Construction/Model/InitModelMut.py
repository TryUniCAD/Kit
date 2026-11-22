from convert.adapters.solidworks.Archive.Construction.Model.EmptyRootRows import (
    EmptyRootRows,
)
from convert.adapters.solidworks.Archive.Construction.Model.MakeModelArrays import (
    MakeModelArrays,
)
from convert.adapters.solidworks.Archive.Construction.Model.MakeModelSeeds import (
    MakeModelSeeds,
)
from convert.adapters.solidworks.Archive.Construction.Model.MakeRelGraph import (
    MakeRelGraph,
)
from convert.adapters.solidworks.Archive.Construction.Model.MakeSelfComp import (
    MakeSelfComp,
)
from convert.adapters.solidworks.Archive.Construction.Model.ModelNulls import (
    KModelNulls,
)
from convert.adapters.solidworks.Archive.Construction.Model.ModelZeroes import (
    KModelZeroes,
)
from convert.adapters.solidworks.Archive.Construction.Model.PartRootRefs import (
    PartRootRefs,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# active new model ownership must be established on the same preallocated root before cyclic references are serialized
def InitModelMut(NodeValue: ArchiveNode, RefsValue: PartRootRefs) -> None:
    FieldsValue = NodeValue.FieldsValue
    FieldsValue.update(MakeModelArrays())
    FieldsValue.update({FieldName: 0 for FieldName in KModelZeroes})
    FieldsValue.update({FieldName: None for FieldName in KModelNulls})
    FieldsValue.update(MakeModelSeeds())
    FlagsValue = FieldsValue["f2c"]
    if type(FlagsValue) is not int:
        raise ValueError("model storage state requires initialized native node flags")
    FieldsValue["f2c"] = FlagsValue | 0x100
    FieldsValue.update(
        {
            "f78": RefsValue.VisualValue,
            "f9b8": RefsValue.DocumentUnits,
            "f9c0": RefsValue.AnalysisUnits,
            "fae0": RefsValue.DetailFields,
            "f990": MakeSelfComp(NodeValue),
            "f9d0": MakeRelGraph(NodeValue),
            "f9f8": tuple({"o": ViewValue} for ViewValue in RefsValue.ViewValues),
        }
    )
    for FieldName in ("f9d8", "fa48", "fa50"):
        FieldsValue[FieldName] = ArchiveNode(
            RuntimeClass("suObList", 1), EmptyRootRows()
        )
