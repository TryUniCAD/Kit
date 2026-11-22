from convert.adapters.solidworks.Core.Writing.Ellipse.CheckEllipPhase import (
    CheckEllipPhase,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import KOraclePart
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


# bracket controls and distinct native process identities qualify the measured family batch
def CheckEllipBatch(Receipt: dict[str, object]) -> tuple[dict[str, object], ...]:
    if (
        Receipt.get("schema") != "kit.sw2026.ordinary-full-ellipse-measurement.v1"
        or ReadMeasMap(Receipt.get("oracle")) != KOraclePart
        or Receipt.get("passed") is not True
        or Receipt.get("healthy_controls") is not True
    ):
        raise ValueError(
            "ellipse measurement requires the exact passing SOLIDWORKS 2026 SP05.2 report"
        )
    TrialHash = ReadMeasSha(Receipt.get("trial_sha256"))
    Phases = ReadMeasRows(Receipt.get("phases"), 68)
    Count = Receipt.get("fresh_processes")
    if (
        type(Count) is not int
        or len(Phases) != Count
        or len(Phases) < 6
        or (len(Phases) - 4) % 2
    ):
        raise ValueError("ellipse measurement lacks the complete native lifetimes")
    Owners = tuple(CheckEllipPhase(PhaseValue, TrialHash) for PhaseValue in Phases)
    Lifetimes = {(ProcessId, Birth) for ProcessId, Birth, _ in Owners}
    RecordHashes = {Digest for _, _, Digest in Owners}
    if len(Phases) != len(Lifetimes) or len(Phases) != len(RecordHashes):
        raise ValueError("ellipse measurement repeats a process or phase receipt")
    Before, After = Phases[:2], Phases[-2:]
    Labels = tuple(Value.get("control") for Value in (*Before, *After))
    if (
        tuple(Value.get("phase") for Value in (*Before, *After))
        != ("before", "before", "after", "after")
        or any(type(Label) is not str or not Label for Label in Labels)
        or Labels[0] == Labels[1]
        or Labels[:2] != Labels[2:]
        or any(
            Value.get("slot") is not None or Value.get("source") is not None
            for Value in (*Before, *After)
        )
    ):
        raise ValueError("ellipse measurement requires both healthy bracket controls")
    return Phases[2:-2]
