from convert.adapters.solidworks.Core.AssemblyWriting.Measured.ReadAsmPhase import (
    ReadAsmPhase,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows


# control and reload evidence must bracket the measured assembly lifecycle in distinct native processes
def CheckAsmPhases(Receipt: dict[str, object]) -> None:
    PhaseRows = ReadMeasRows(Receipt.get("phases"), 4)
    if tuple(RowValue.get("mode") for RowValue in PhaseRows) != (
        "before",
        "generated",
        "reopen",
        "after",
    ):
        raise ValueError(
            "native assembly measurement requires both controls and a fresh reopen"
        )
    Phases = tuple(ReadAsmPhase(Value) for Value in PhaseRows)
    if (
        len({Identity for Identity, _, _, _ in Phases}) != len(Phases)
        or len({Digest for _, Digest, _, _ in Phases}) != len(Phases)
        or any(Start >= Finish for _, _, Start, Finish in Phases)
        or any(Earlier[3] > Later[2] for Earlier, Later in zip(Phases, Phases[1:]))
    ):
        raise ValueError(
            "native assembly measurement repeats or overlaps an oracle lifetime"
        )
