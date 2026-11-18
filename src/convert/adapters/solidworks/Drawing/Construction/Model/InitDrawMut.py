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
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Drawing.Construction.Model.DrawRootRefs import (
    DrawRootRefs,
)


# drawing model initialization must retain its actual self ownership while omitting part only visual and analysis state
def InitDrawMut(NodeValue: ArchiveNode, RefsValue: DrawRootRefs) -> None:
    RequireRootNode(NodeValue, "moDrawing_c")
    FieldsValue = NodeValue.FieldsValue
    FieldsValue.update(MakeModelArrays())
    FieldsValue.update(dict.fromkeys(KModelZeroes, 0))
    FieldsValue.update(dict.fromkeys(KModelNulls, None))
    FieldsValue.update(MakeModelSeeds())
    FieldsValue.update(
        {
            "f2c": 256,
            "f78": None,
            "f9c0": None,
            "fae0": RefsValue.DetailFields,
            "f9b8": RefsValue.DocumentUnits,
            "f990": MakeSelfComp(NodeValue),
            "f9d0": MakeRelGraph(NodeValue),
            "f9f8": tuple({"o": ViewValue} for ViewValue in RefsValue.ViewValues),
            "fd50": 0,
        }
    )
    for FieldName in ("f9d8", "fa48", "fa50"):
        FieldsValue[FieldName] = ArchiveNode(
            RuntimeClass("suObList", 1), EmptyRootRows()
        )
