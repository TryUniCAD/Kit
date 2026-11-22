from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.CheckAsmMeta import (
    CheckAsmMeta,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.AsmDisplayIn import (
    AsmDisplayIn,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.EmitAsmStreams import (
    EmitAsmStreams,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Headers.MakeAsmHeaders import (
    MakeAsmHeaders,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.MakeAsmBase import (
    MakeAsmBase,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.PutPartRefsMut import (
    PutPartRefsMut,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.CheckGroupChild import (
    CheckGroupChild,
)
from convert.adapters.solidworks.Archive.Construction.AssemblySets.OrderedAsm import (
    OrderedAsm,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CheckCylNames import (
    CheckCylNames,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylMateCtx import (
    CylMateCtx,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylMateIn import (
    CylMateIn,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.MakeCylMateMut import (
    MakeCylMateMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Container.Container import BuildSldprt


# the concentric parent shares the regular assembly container and links both occurrences to its single owned child
def MakeCylAsm(
    ChildValue: PartCandidate,
    InputValue: AssemblyInput,
    Occurrences: tuple[OccurrenceIn, OccurrenceIn],
    EndIndexes: tuple[int, int],
    FaceTag: int,
    IntentValue: CylMateIn,
    *,
    DisplayValues: tuple[AsmDisplayIn, ...] | None = None,
) -> OrderedAsm:
    CheckAsmMeta(InputValue)
    CheckGroupChild(ChildValue, InputValue)
    if (
        len(CastValue(tuple[object, ...], Occurrences)) != 2
        or any(type(Value) is not OccurrenceIn for Value in Occurrences)
        or any(type(Value) is not int for Value in EndIndexes)
        or EndIndexes not in ((0, 1), (1, 0))
    ):
        raise ValueError(
            "concentric parent requires two distinct ordered direct occurrences"
        )
    CheckCylNames(InputValue, Occurrences, IntentValue)
    StateValue = MakeAsmBase(InputValue)
    HeadersValue = MakeAsmHeaders(StateValue, InputValue)
    References = PutPartRefsMut(
        StateValue, ChildValue, InputValue, Occurrences, HeadersValue
    )
    First, Second = EndIndexes
    MateValue = MakeCylMateMut(
        CylMateCtx(StateValue, InputValue, ChildValue, HeadersValue),
        (References[First], References[Second]),
        (Occurrences[First].FrameValue, Occurrences[Second].FrameValue),
        FaceTag,
        IntentValue,
    )
    StreamsValue = EmitAsmStreams(
        StateValue,
        ChildValue,
        InputValue,
        HeadersValue,
        References,
        MateValue,
        DisplayValues=DisplayValues,
    )
    return OrderedAsm(
        StateValue,
        ChildValue,
        References,
        (MateValue,),
        HeadersValue[0],
        HeadersValue[1],
        StreamsValue.ManagerHeader,
        StreamsValue.DefinitionValue,
        StreamsValue.ConfigValue,
        StreamsValue.ResolvedValue,
        StreamsValue.MatesValue,
        StreamsValue.StreamsValue,
        BuildSldprt(StreamsValue.StreamsValue, FormatVersion=4),
    )
