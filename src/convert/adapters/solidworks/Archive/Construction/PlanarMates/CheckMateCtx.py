from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTime import (
    FeatureTime,
)
from convert.adapters.solidworks.Archive.Construction.OrderedMates.CheckMateState import (
    CheckMateState,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MateContext import (
    MateContext,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CheckMateIds import (
    CheckMateIds,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.PlanarMateIn import (
    PlanarMateIn,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
    RequireRecord,
)


# native construction needs a fresh owned two occurrence assembly and an explicit supported authored relationship
def CheckMateCtx(
    Context: MateContext, InputValue: PlanarMateIn
) -> tuple[ArchiveNode, ArchiveNode]:
    Assembly = RequireNode(Context.AssemblyValue, "moAssembly_c")
    Group = RequireNode(Context.GroupValue, "moMateGroup_c")
    Header = RequireNode(Context.HeaderValue, "moHeader_c")
    Configuration = RequireNode(Context.ConfigValue, "moConfiguration_c")
    if (
        Group.FieldsValue.get("owner") is not Assembly
        or Configuration.FieldsValue.get("owner") is not Assembly
        or not Header.FieldsValue.get("fec")
    ):
        raise ValueError(
            "mate factory requires actual parent group configuration and model header"
        )
    if ReadRows(
        RequireRecord(RequireRecord(Group.FieldsValue.get("f60")).get("list")).get(
            "items"
        )
    ):
        raise ValueError(
            "mate group wire children must stay separate from the mate stream"
        )
    if (
        InputValue.KindValue not in ("coincident", "parallel")
        or len(InputValue.Selections) != 2
    ):
        raise ValueError(
            "mate factory admits coincident or parallel with two selected principal planes"
        )
    Items = ReadRows(
        RequireRecord(RequireRecord(Assembly.FieldsValue.get("f68")).get("list")).get(
            "items"
        )
    )
    if len(Items) != 2:
        raise ValueError("ordinary mate construction requires two direct occurrences")
    First, Second = (RequireNode(Value.get("o"), "moReference_c") for Value in Items)
    CheckMateIds(Context, (First, Second))
    if (
        First is Second
        or FieldInt(First.FieldsValue, "f08") == FieldInt(Second.FieldsValue, "f08")
        or not any(InputValue.FixedValue is Value for Value in (First, Second))
    ):
        raise ValueError("mate fixed input or occurrence identities are ambiguous")
    CheckMateState(Context, InputValue, (First, Second))
    if (
        InputValue.Selections[0].OccurrenceValue
        is InputValue.Selections[1].OccurrenceValue
    ):
        raise ValueError("mate selections require distinct actual occurrences")
    Counter = FieldInt(Assembly.FieldsValue, "fd48")
    if not 0 <= Counter <= 0x7FFFFFFD:
        raise ValueError(
            "assembly wrapper counter cannot allocate two resolved references"
        )
    _ = FeatureTime(InputValue.CreatedValue)
    return First, Second
