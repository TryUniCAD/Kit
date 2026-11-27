from typing import cast as CastValue


# shared display construction must preserve the exact authored boolean and signed leader domains across native owner families
def CheckViewArgs(DesignIntent: bool, SelectedLeader: int) -> None:
    if (
        type(CastValue(object, DesignIntent)) is not bool
        or type(CastValue(object, SelectedLeader)) is not int
        or not -(1 << 31) <= SelectedLeader < (1 << 31)
    ):
        raise ValueError(
            "display presentation requires an authored boolean and signed leader value"
        )
