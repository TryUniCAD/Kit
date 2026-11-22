from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows


# each phase must witness clean open and rebuild plus every recorded numerical result
def CheckRevPhase(Phase: dict[str, object], Rebuilds: int) -> None:
    Before = ReadMeasMap(Phase.get("before_explicit_rebuild"))
    Calls = ReadMeasRows(Phase.get("api_calls"), 512)
    Checks = ReadMeasRows(Phase.get("checks"), 32)
    Builds = tuple(RowValue.get("result") for RowValue in Calls if RowValue.get("method") == "ForceRebuild3")
    if (
        any(Phase.get(Field) is not True for Field in ("passed", "inspection_completed", "source_immutable"))
        or Phase.get("first_failure") is not None
        or ReadMeasMap(Phase.get("open_status")) != {"opened": True, "errors": 0, "warnings": 0}
        or Before.get("whats_wrong") != 0
        or len(Builds) != Rebuilds
        or any(Value is not True for Value in Builds)
        or len(Checks) < 12 * Rebuilds
        or any(RowValue.get("passed") is not True for RowValue in Checks)
    ):
        raise ValueError("measured revolve has an incomplete native observation phase")
