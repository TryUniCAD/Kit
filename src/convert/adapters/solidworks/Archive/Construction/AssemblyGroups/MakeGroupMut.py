from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.RecordMateMut import (
    RecordMateMut,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.GroupMateIn import (
    GroupMateIn,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.PlanarDistance.MakeDistMateMut import (
    MakeDistMateMut,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MakeMateMut import (
    MakeMateMut,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MateChild import (
    MateChild,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MateContext import (
    MateContext,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MateSelection import (
    MateSelection,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.PlanarMateIn import (
    PlanarMateIn,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# each group mate must consume its two authored actual occurrence and child datum selections through the same measured native wrapper and dimension factories
def MakeGroupMut(
    StateValue: AssemblyState,
    ChildValue: PartCandidate,
    InputValue: AssemblyInput,
    MateValue: GroupMateIn,
    Occurrences: tuple[ArchiveNode, ...],
    HeadersValue: tuple[ArchiveNode, ArchiveNode],
    PreviousValues: tuple[ArchiveNode, ...],
    FixedIndex: int,
) -> ArchiveNode:
    ChildGraph = MateChild(
        ChildValue.SystemValue.RootValue,
        ChildValue.HeaderValue,
        ChildValue.CurrentConfig,
        tuple(
            ArchiveNode.RequireNode(Value)
            for Value in ChildValue.ResolvedValue.RootsValue
        ),
    )
    First, Second = tuple(
        MateSelection(
            Occurrences[Value.OccurrenceIndex],
            ChildGraph,
            ChildValue.SystemValue.SystemValues.PlaneValues[Value.AxisValue],
        )
        for Value in MateValue.EndValues
    )
    Context = MateContext(
        StateValue.RootValue,
        StateValue.GroupValue,
        HeadersValue[0],
        StateValue.CurrentConfig,
        InputValue.TargetValue,
        StateValue.Allocator,
        PreviousValues,
    )
    NativeInput = PlanarMateIn(
        MateValue.KindValue,
        MateValue.NameValue,
        (First, Second),
        Occurrences[FixedIndex],
        (
            InputValue.HeaderValue.CreatedAt
            if MateValue.CreatedAt is None
            else MateValue.CreatedAt
        ),
    )
    NodeValue = (
        MakeMateMut(Context, NativeInput)
        if MateValue.DistanceValue is None
        else MakeDistMateMut(Context, NativeInput, MateValue.DistanceValue)
    )
    RecordMateMut(
        StateValue, InputValue, NodeValue, HeadersValue, CreatedAt=MateValue.CreatedAt
    )
    return NodeValue
