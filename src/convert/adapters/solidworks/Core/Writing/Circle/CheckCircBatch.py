from convert.adapters.solidworks.Core.Writing.Circle.ReadCircState import ReadCircVec
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasNum import ReadMeasNum
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


# a process must have a real creation event as well as its recyclable session pid
def ReadCircLife(RowValue: dict[str, object]) -> tuple[int, int]:
    Process = ReadMeasMap(RowValue.get("process"))
    Birth = Process.get("process_creation_filetime")
    PidValue = Process.get("process_id")
    if (
        type(Birth) is not int
        or Birth <= 0
        or type(PidValue) is not int
        or PidValue <= 0
    ):
        raise ValueError("circle measurement requires its fresh process identity")
    return Birth, PidValue


# both bounding controls need observation of healthy actual solid geometry
def CircControls(Receipt: dict[str, object]) -> tuple[tuple[int, int], ...]:
    RowsValue = ReadMeasRows(Receipt.get("controls"), 2)
    if tuple(RowValue.get("kind") for RowValue in RowsValue) != (
        "control_before",
        "control_after",
    ):
        raise ValueError("circle measurement requires both ordered bracket controls")
    Before, After = RowsValue
    if Before.get("sha256") != After.get("sha256"):
        raise ValueError("circle brackets require the same actual native control")
    for RowValue in RowsValue:
        if (
            RowValue.get("healthy") is not True
            or type(RowValue.get("bodies")) is not int
            or RowValue["bodies"] != 1
            or type(RowValue.get("whats_wrong")) is not int
            or RowValue["whats_wrong"] != 0
        ):
            raise ValueError("circle measurement has an unhealthy native control")
        MassValue = ReadMeasMap(RowValue.get("mass"))
        _ = ReadMeasNum(MassValue.get("volume"))
        _ = ReadMeasNum(MassValue.get("area"))
        _ = ReadMeasNum(MassValue.get("mass"))
        _ = ReadCircVec(MassValue.get("com"), 3)
        _ = ReadMeasSha(RowValue.get("sha256"))
    return tuple(ReadCircLife(RowValue) for RowValue in RowsValue)


# numerical coverage and reported freshness must match the actual linked phase rows
def CheckCircBatch(Receipt: dict[str, object]) -> None:
    Controls = CircControls(Receipt)
    Cases = ReadMeasRows(Receipt.get("cases"), 32)
    Phases = tuple(
        PhaseValue
        for CaseValue in Cases
        for PhaseValue in ReadMeasRows(CaseValue.get("stages"), 3)
    )
    LifeValues = tuple(ReadCircLife(Phase) for Phase in Phases)
    AllLives = (*Controls, *LifeValues)
    ExpectedCounts = tuple(Phase.get("numeric_checks") for Phase in Phases)
    if not Cases or any(
        type(Count) is not int or Count < 1 for Count in ExpectedCounts
    ):
        raise ValueError("circle measurement lacks numerical observations")
    Checks = sum(ReadMeasNum(Count) for Count in ExpectedCounts)
    Digests = {ReadMeasSha(Phase.get("record_sha256")) for Phase in Phases}
    if (
        len(Phases) != 3 * len(Cases)
        or len(Digests) != len(Phases)
        or len(set(AllLives)) != len(AllLives)
        or Receipt.get("distinct_processes") != len(AllLives)
        or Receipt.get("candidate_numeric_checks") != Checks
        or any(not Controls[0][0] < Stamp[0] < Controls[1][0] for Stamp in LifeValues)
    ):
        raise ValueError(
            "circle native phases require distinct measured bracketed lifetimes"
        )
