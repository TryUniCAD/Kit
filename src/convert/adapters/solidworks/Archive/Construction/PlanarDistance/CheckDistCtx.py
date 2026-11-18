from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTime import (
    FeatureTime,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CheckMateIds import (
    CheckMateIds,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MateContext import (
    MateContext,
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


# distance mates require their explicit concrete input and the same actual fresh parent publication boundary without aliasing another mate kind
def CheckDistCtx(
    Context: MateContext, InputValue: PlanarMateIn
) -> tuple[ArchiveNode, ArchiveNode]:
    Assembly = RequireNode(Context.AssemblyValue, "moAssembly_c")
    GroupValue = RequireNode(Context.GroupValue, "moMateGroup_c")
    Header = RequireNode(Context.HeaderValue, "moHeader_c")
    Configuration = RequireNode(Context.ConfigValue, "moConfiguration_c")
    if (
        GroupValue.FieldsValue.get("owner") is not Assembly
        or Configuration.FieldsValue.get("owner") is not Assembly
        or not Header.FieldsValue.get("fec")
    ):
        raise ValueError(
            "distance mate requires its actual parent group configuration and model header"
        )
    if ReadRows(
        RequireRecord(RequireRecord(GroupValue.FieldsValue.get("f60")).get("list")).get(
            "items"
        )
    ):
        raise ValueError(
            "distance mate group wire children must stay separate from its mate stream"
        )
    if InputValue.KindValue != "distance" or len(InputValue.Selections) != 2:
        raise ValueError(
            "distance factory requires two explicit selected principal planes"
        )
    ItemsValue = ReadRows(
        RequireRecord(RequireRecord(Assembly.FieldsValue.get("f68")).get("list")).get(
            "items"
        )
    )
    if len(ItemsValue) != 2:
        raise ValueError("distance factory requires two direct part occurrences")
    Occurrences = tuple(
        RequireNode(Value.get("o"), "moReference_c") for Value in ItemsValue
    )
    First, Second = Occurrences
    CheckMateIds(Context, (First, Second))
    if First is Second or not any(
        InputValue.FixedValue is Value for Value in Occurrences
    ):
        raise ValueError(
            "distance fixed input and occurrence identities must be actual distinct parent members"
        )
    if any(
        FieldInt(Value.FieldsValue, "f400") != 3
        or FieldInt(Value.FieldsValue, "f408") != 0
        for Value in Occurrences
    ):
        raise ValueError("distance factory requires fresh solve and fixed states")
    if (
        InputValue.Selections[0].OccurrenceValue
        is InputValue.Selections[1].OccurrenceValue
    ):
        raise ValueError("distance selections require two distinct actual occurrences")
    if not 0 <= FieldInt(Assembly.FieldsValue, "fd48") <= 0x7FFFFFFD:
        raise ValueError("distance wrapper counter cannot allocate two references")
    _ = FeatureTime(InputValue.CreatedValue)
    return First, Second
