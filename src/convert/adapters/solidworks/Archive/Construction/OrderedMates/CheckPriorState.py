from convert.adapters.solidworks.Archive.Construction.OrderedMates.CheckPriorWraps import (
    CheckPriorWraps,
)
from convert.adapters.solidworks.Archive.Construction.OrderedMates.ReadPriorIds import (
    ReadPriorIds,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MateContext import (
    MateContext,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.PlanarMateIn import (
    PlanarMateIn,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadLogItems import (
    ReadLogItems,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)


# continuation requires actual prior created mates complete header publication independent allocation and the same fixed anchor without resetting existing occurrence state
def CheckPriorState(
    Context: MateContext,
    InputValue: PlanarMateIn,
    Occurrences: tuple[ArchiveNode, ...],
) -> None:
    if type(Context.PreviousValues) is not tuple:
        raise ValueError("ordered prior mates require their actual immutable sequence")
    Identifiers: list[int] = []
    MateIds: list[int] = []
    MateNames: list[str] = []
    for IndexValue, MateValue in enumerate(Context.PreviousValues):
        if (
            MateValue.ClassValue
            not in tuple(
                RuntimeClass(NameValue, 1)
                for NameValue in (
                    "moMateCoincident",
                    "moMateParallel",
                    "moMateDistanceDim_c",
                )
            )
            or MateValue.FieldsValue.get("owner") is not Context.GroupValue
        ):
            raise ValueError(
                "ordered continuation contains an unsupported or differently owned prior mate"
            )
        if tuple(
            FieldInt(MateValue.FieldsValue, NameValue)
            for NameValue in ("f0c", "f3b4", "f3b8")
        ) != (1, 1, 0):
            raise ValueError(
                "ordered continuation requires fresh generated aligned unsolved prior mate state"
            )
        CheckPriorWraps(Context, MateValue, IndexValue, Occurrences)
        Identifiers.extend(ReadPriorIds(MateValue, Context.Allocator))
        MateIds.append(FieldInt(MateValue.FieldsValue, "f08"))
        MateNames.append(ReadNodeName(MateValue))
    if (
        len(set(Identifiers)) != len(Identifiers)
        or Identifiers != sorted(Identifiers)
        or not Identifiers
        or Identifiers[-1] + 1 != Context.Allocator.NextValue
    ):
        raise ValueError(
            "ordered prior persistent allocation is incomplete or ambiguous"
        )
    ParentIds = tuple(
        FieldInt(Value.FieldsValue, "f08")
        for Value in (Context.AssemblyValue, Context.GroupValue, *Occurrences)
    )
    if Identifiers[0] <= max(ParentIds):
        raise ValueError(
            "ordered prior mate or dimension collides with existing parent identifiers"
        )
    if len(set((*MateNames, InputValue.NameValue))) != len(MateNames) + 1:
        raise ValueError("ordered mate names must be distinct")
    if (
        FieldInt(Context.AssemblyValue.FieldsValue, "fd48")
        != 2 * len(Context.PreviousValues)
        or FieldInt(Context.ConfigValue.FieldsValue, "f85c")
        != Context.Allocator.NextValue - 1
    ):
        raise ValueError(
            "ordered prior wrapper allocation or configuration publication differs"
        )
    LogsValue = ReadLogItems(Context.HeaderValue.FieldsValue["f20"], "moLogs_c")
    if tuple(FieldInt(Value.FieldsValue, "f48") for Value in LogsValue) != (
        FieldInt(Context.AssemblyValue.FieldsValue, "f08"),
        *MateIds,
    ):
        raise ValueError("ordered prior mate creation logs are missing or misordered")
