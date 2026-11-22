from convert.adapters.solidworks.Core.Writing.Measured.CheckMeasPhase import (
    CheckMeasPhase,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import KOraclePart
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from convert.adapters.solidworks.Core.Writing.Sweeps.CheckSwControl import (
    CheckSwControl,
)
from convert.adapters.solidworks.Core.Writing.Sweeps.SweepMeasPhases import (
    KSwMeasPhases,
)


# a disclosed sweep report must bind two complete lifecycles in fresh controlled processes
def CheckSwBatch(Receipt: dict[str, object]) -> tuple[dict[str, object], ...]:
    if (
        Receipt.get("schema") != "kit.sw2026.standard-sweep-measurement.v1"
        or ReadMeasMap(Receipt.get("oracle")) != KOraclePart
        or Receipt.get("passed") is not True
        or Receipt.get("healthy_controls") is not True
    ):
        raise ValueError(
            "sweep measurement requires the exact passing SOLIDWORKS 2026 SP05.2 report"
        )
    TrialHash = ReadMeasSha(Receipt.get("trial_sha256"))
    ControlHash = ReadMeasSha(Receipt.get("control_sha256"))
    PhaseCount = 2 * len(KSwMeasPhases) + 2
    Phases = ReadMeasRows(Receipt.get("phases"), PhaseCount)
    if (
        type(Receipt.get("fresh_processes")) is not int
        or len(Phases) != Receipt["fresh_processes"]
        or len(Phases) != PhaseCount
    ):
        raise ValueError("sweep measurement lacks the complete native lifetimes")
    Owners = tuple(CheckMeasPhase(Phase, TrialHash) for Phase in Phases)
    if len(Phases) != len({Owner[:2] for Owner in Owners}) or len(Phases) != len(
        {Owner[2] for Owner in Owners}
    ):
        raise ValueError("sweep measurement repeats a process or phase receipt")
    CheckSwControl(Phases[0], "control-before", ControlHash)
    CheckSwControl(Phases[-1], "control-after", ControlHash)
    if any(
        Earlier[1] >= Later[1]
        for Earlier, Later in zip(Owners[:-1], Owners[1:], strict=True)
    ):
        raise ValueError("sweep measurement lifetimes are out of creation order")
    return Phases[1:-1]
