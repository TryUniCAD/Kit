from typing import cast as CastValue
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


# exact native receipts bracket all measurements with the known passing control phases
def MeasPhaseMap(Receipt: dict[str, object]) -> dict[str, dict[str, object]]:
    PhaseRows = ReadMeasRows(Receipt.get("phases"))
    PhaseCount = Receipt.get("distinct_native_processes")
    if type(PhaseCount) is not int or PhaseCount != len(PhaseRows) or PhaseCount < 4:
        raise ValueError(
            "native measurement requires distinct fresh processes and both controls"
        )
    Reports: dict[str, dict[str, object]] = {}
    Digests: set[str] = set()
    for PhaseValue in PhaseRows:
        Label = PhaseValue.get("role")
        Digest = ReadMeasSha(PhaseValue.get("record_sha256"))
        CheckCount = PhaseValue.get("numeric_checks")
        if (
            type(Label) is not str
            or not Label
            or Label in Reports
            or Digest in Digests
            or PhaseValue.get("passed") is not True
            or type(CheckCount) is not int
            or CheckCount < 0
        ):
            raise ValueError("native measurement repeats or failed an oracle phase")
        Reports[Label] = PhaseValue
        Digests.add(Digest)
    Labels = tuple(Reports)
    if (Labels[0], Labels[-1]) != ("ControlBefore", "ControlAfter"):
        raise ValueError("native measurement phases must be bracketed by both controls")
    for Label in (Labels[0], Labels[-1]):
        Control = Reports[Label]
        if (
            Control.get("states") != []
            or Control.get("save_status") is not None
            or Control.get("derivative_sha256") is not None
        ):
            raise ValueError(
                "native measurement has the wrong model in a control phase"
            )
    TotalChecks = Receipt.get("numeric_checks")
    if type(TotalChecks) is not int or TotalChecks != sum(
        CastValue(int, Value["numeric_checks"]) for Value in PhaseRows
    ):
        raise ValueError("native measurement numerical coverage is inconsistent")
    return Reports
