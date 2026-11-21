from convert.adapters.solidworks.Archive.Construction.Model.MakeSelfComp import (
    MakeSelfComp,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import (
    CompRefFields,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# the first stock body selection must identify its real base feature and atom without transmitting kernel references
def MakeBodyRef(
    RootValue: ArchiveNode, FeatureValue: ArchiveNode, AtomValue: ArchiveNode
) -> ArchiveNode:
    FieldsValue = CompRefFields(MakeSelfComp(RootValue))
    AtomId = FieldInt(AtomValue.FieldsValue, "f140")
    LineageValue = [{"v": AtomId}]
    FieldsValue.update(
        f18=AtomId,
        f1c=AtomId,
        ff0=None,
        n110=len(LineageValue),
        f110=LineageValue,
        f108=FieldInt(FeatureValue.FieldsValue, "f08"),
        f104=0,
        f100=0,
    )
    return ArchiveNode(RuntimeClass("moCompSolidBody_c", 1), FieldsValue)
