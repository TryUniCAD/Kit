from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasNum import ReadMeasNum
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


# a real native observation needs a clean open and an independently identified lifetime
def ReadAsmPhase(
    RowValue: dict[str, object],
) -> tuple[tuple[int, int], str, float, float]:
    ProcessId = RowValue.get("process_id")
    CreationTime = RowValue.get("process_creation_filetime")
    Errors = RowValue.get("open_errors")
    Warnings = RowValue.get("open_warnings")
    if (
        RowValue.keys()
        != {
            "mode",
            "passed",
            "open_errors",
            "open_warnings",
            "process_id",
            "process_creation_filetime",
            "record_sha256",
            "started_at",
            "finished_at",
        }
        or RowValue.get("passed") is not True
        or type(Errors) is not int
        or type(Warnings) is not int
        or Errors != 0
        or Warnings != 0
        or type(ProcessId) is not int
        or type(CreationTime) is not int
        or not 0 < ProcessId <= 0xFFFFFFFF
        or not 0 < CreationTime <= 0xFFFFFFFFFFFFFFFF
    ):
        raise ValueError(
            "native assembly measurement has an unclean or unidentified phase"
        )
    return (
        (ProcessId, CreationTime),
        ReadMeasSha(RowValue.get("record_sha256")),
        ReadMeasNum(RowValue.get("started_at")),
        ReadMeasNum(RowValue.get("finished_at")),
    )
