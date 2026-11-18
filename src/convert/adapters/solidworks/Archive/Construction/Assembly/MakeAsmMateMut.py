from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyMateIn import (
    AssemblyMateIn,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.RecordMateMut import (
    RecordMateMut,
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


# the complete assembly reuses qualified ordinary mate factories with the actual generated child datum and publishes only real mate revision events
def MakeAsmMateMut(
    StateValue: AssemblyState,
    ChildValue: PartCandidate,
    InputValue: AssemblyInput,
    MateValue: AssemblyMateIn,
    Occurrences: tuple[ArchiveNode, ArchiveNode],
    HeadersValue: tuple[ArchiveNode, ArchiveNode],
    PreviousValues: tuple[ArchiveNode, ...] = (),
) -> ArchiveNode:
    ChildGraph = MateChild(
        ChildValue.SystemValue.RootValue,
        ChildValue.HeaderValue,
        ChildValue.CurrentConfig,
        tuple(
            ArchiveNode.RequireNode(NodeValue)
            for NodeValue in ChildValue.ResolvedValue.RootsValue
        ),
    )
    DatumValue = ChildValue.SystemValue.SystemValues.PlaneValues[MateValue.AxisValue]
    First = MateSelection(Occurrences[0], ChildGraph, DatumValue)
    Second = MateSelection(Occurrences[1], ChildGraph, DatumValue)
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
        Occurrences[MateValue.FixedIndex],
        InputValue.HeaderValue.CreatedAt,
    )
    if MateValue.DistanceValue is None:
        NodeValue = MakeMateMut(Context, NativeInput)
    else:
        NodeValue = MakeDistMateMut(Context, NativeInput, MateValue.DistanceValue)
    RecordMateMut(StateValue, InputValue, NodeValue, HeadersValue)
    return NodeValue
