from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTime import (
    FeatureTime,
)
from convert.adapters.solidworks.Archive.Construction.OrderedMates.CheckMateState import (
    CheckMateState,
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
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadMateOccs import (
    ReadMateOccs,
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
    Occurrences = ReadMateOccs(Assembly)
    CheckMateIds(Context, Occurrences)
    if not any(InputValue.FixedValue is Value for Value in Occurrences):
        raise ValueError(
            "distance fixed input and occurrence identities must be actual distinct parent members"
        )
    CheckMateState(Context, InputValue, Occurrences)
    First, Second = (Value.OccurrenceValue for Value in InputValue.Selections)
    if First is Second or any(
        not any(Value is Member for Member in Occurrences) for Value in (First, Second)
    ):
        raise ValueError("distance selections require two distinct actual occurrences")
    if not 0 <= FieldInt(Assembly.FieldsValue, "fd48") <= 0x7FFFFFFD:
        raise ValueError("distance wrapper counter cannot allocate two references")
    _ = FeatureTime(InputValue.CreatedValue)
    return First, Second
