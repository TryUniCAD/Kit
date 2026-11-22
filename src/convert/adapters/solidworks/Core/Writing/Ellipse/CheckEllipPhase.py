from typing import cast as CastValue

from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


# each phase must own a successful measured process with its own receipt and creation time
def CheckEllipPhase(
    PhaseValue: dict[str, object], TrialHash: str
) -> tuple[int, int, str]:
    Process = PhaseValue.get("lifetime")
    CodeValue = PhaseValue.get("exit_code")
    CheckCount = PhaseValue.get("checks")
    if (
        type(Process) is not list
        or len(CastValue(list[object], Process)) != 2
        or any(
            type(ItemValue) is not int or ItemValue <= 0
            for ItemValue in CastValue(list[object], Process)
        )
        or PhaseValue.get("trial_sha256") != TrialHash
        or PhaseValue.get("passed") is not True
        or type(CodeValue) is not int
        or CodeValue != 0
        or type(CheckCount) is not int
        or CheckCount < 0
    ):
        raise ValueError("ellipse measurement has a failed or unowned native phase")
    ProcessId, BirthEvent = CastValue(list[int], Process)
    return ProcessId, BirthEvent, ReadMeasSha(PhaseValue.get("receipt_sha256"))
