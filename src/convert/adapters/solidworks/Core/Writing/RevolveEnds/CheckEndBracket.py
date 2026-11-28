from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


# native candidate outcomes only qualify inside their own healthy fresh process bracket
def CheckEndBracket(ResultValue: dict[str, object]) -> tuple[str, ...]:
    if (
        ResultValue.get("controls_unchanged") is not True
        or ResultValue.get("application_idle") is not True
        or ResultValue.get("distinct_processes") != 10
    ):
        raise ValueError("measured revolve ends require a healthy native bracket")
    Controls = tuple(
        ReadMeasMap(ResultValue.get(RoleValue))
        for RoleValue in ("control-before", "control-after")
    )
    PhaseDigests = tuple(
        ReadMeasSha(ControlRow.get("sha256")) for ControlRow in Controls
    )
    if len(set(PhaseDigests)) != 2 or any(
        ControlRow.get("passed") is not True for ControlRow in Controls
    ):
        raise ValueError("measured revolve ends require a healthy native bracket")
    return PhaseDigests
