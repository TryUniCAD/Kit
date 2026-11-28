from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeObList import (
    MakeObList,
)
from convert.adapters.solidworks.Archive.Construction.Model.EmptyRootRows import (
    EmptyRootRows,
)
from convert.adapters.solidworks.Archive.Construction.Part.Equations.MakeEqDimension import (
    MakeEqDimension,
)
from convert.adapters.solidworks.Archive.Construction.Part.Equations.MakeEqToken import (
    MakeEqToken,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    RequireNode,
    RequireRecord,
)


# the relation manager must own one complete expression and both sides must bind the actual live dimensions
def BindWidthMut(
    RootValue: ArchiveNode, WidthValue: DimensionGraph, DepthValue: DimensionGraph
) -> None:
    ManagerValue = RequireNode(RootValue.FieldsValue["f9d0"], "moRelMgr_c").FieldsValue
    if RequireRecord(ManagerValue["f58"]) != EmptyRootRows():
        raise ValueError("local equation requires an empty part relation manager")
    WidthOwner = ArchiveNode.RequireNode(WidthValue.HandleValue.FieldsValue["owner"])
    DepthOwner = ArchiveNode.RequireNode(DepthValue.HandleValue.FieldsValue["owner"])
    WidthText = (
        f'"{ReadNodeName(WidthValue.ParameterValue)}@{ReadNodeName(WidthOwner)}"'
    )
    DepthText = (
        f'"{ReadNodeName(DepthValue.ParameterValue)}@{ReadNodeName(DepthOwner)}"'
    )
    RightText = f" = {WidthText} / 2"
    RelationId = FieldInt(ManagerValue, "ff4") + 1
    RelationValue = ArchiveNode(
        RuntimeClass("moRelation_c", 1),
        {
            "f10": DepthText + RightText,
            "f18": 1 << 9,
            "f48": 0,
            "f74": 0,
            "f08": RelationId,
            "f38": "uuUNDEFINED",
            "f88": 0,
            "f6c": 0,
            "f8c": 0,
        },
    )
    LeftTokens = MakeObList(MakeEqDimension(RootValue, DepthValue, DepthText, 0))
    RightTokens = MakeObList(
        MakeEqToken("moRelOperator_c", "=", 0, 3),
        MakeEqDimension(RootValue, WidthValue, WidthText, 2),
        MakeEqToken("moRelOperator_c", "/", len(WidthText) + 3, 3),
        MakeEqToken("moRelValue_c", "2", len(WidthText) + 5, 2),
    )
    for FieldName, SideText, TokenList, IsLeft in (
        ("f58", DepthText, LeftTokens, 1),
        ("f60", RightText, RightTokens, 0),
    ):
        RelationValue.FieldsValue[FieldName] = ArchiveNode(
            RuntimeClass("moRelEquationSide_c", 1),
            {
                "f10": TokenList,
                "f50": SideText,
                "f58": 0,
                "f98": IsLeft,
                "fa0": RelationValue,
            },
        )
    ManagerValue.update(f58=MakeObList(RelationValue), ff4=RelationId, f150=1)
