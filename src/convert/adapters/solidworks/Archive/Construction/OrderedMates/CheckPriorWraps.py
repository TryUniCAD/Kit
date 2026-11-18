from convert.adapters.solidworks.Archive.Construction.PlanarMates.MateContext import (
    MateContext,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
)


# each prior mate must retain its own ordered wrapper ids and actual parent occurrence backlinks before the next owner counter can be consumed
def CheckPriorWraps(
    Context: MateContext,
    MateValue: ArchiveNode,
    MateIndex: int,
    Occurrences: tuple[ArchiveNode, ArchiveNode],
) -> None:
    Wrappers = ReadRows(MateValue.FieldsValue.get("f410"))
    if len(Wrappers) != 2:
        raise ValueError(
            "ordered mate continuation requires two prior resolved wrappers"
        )
    References: list[ArchiveNode] = []
    for IndexValue, RowValue in enumerate(Wrappers):
        Wrapper = RequireNode(RowValue.get("o"), "moPlaneRef_w")
        if tuple(
            FieldInt(Wrapper.FieldsValue, NameValue)
            for NameValue in ("f74", "f78", "f7c")
        ) != (
            FieldInt(MateValue.FieldsValue, "f08"),
            2 * MateIndex + IndexValue,
            IndexValue,
        ):
            raise ValueError("ordered prior mate wrapper allocation differs")
        Reference = RequireNode(Wrapper.FieldsValue.get("f58"), "moCompRefPlane_c")
        Component = RequireNode(Reference.FieldsValue.get("f58"), "moChainComponent_c")
        ChainValue = RequireNode(Component.FieldsValue.get("f20"), "moReferenceChain_c")
        Targets = RequireNode(ChainValue.FieldsValue.get("f08"), "moExtFeatureList_c")
        TargetRows = ReadRows(Targets.FieldsValue.get("f08"))
        if (
            len(TargetRows) != 1
            or Component.FieldsValue.get("owner") is not Context.AssemblyValue
        ):
            raise ValueError("ordered prior mate lost its actual containing model path")
        External = RequireNode(TargetRows[0].get("o"), "moExtFeature_c")
        Occurrence = RequireNode(External.FieldsValue.get("f50"), "moReference_c")
        if (
            not any(Occurrence is Value for Value in Occurrences)
            or Occurrence.FieldsValue.get("f4f8") is not External
        ):
            raise ValueError("ordered prior mate targets a different occurrence graph")
        References.append(Occurrence)
    if References[0] is References[1]:
        raise ValueError("ordered prior mate reused one occurrence for both endpoints")
