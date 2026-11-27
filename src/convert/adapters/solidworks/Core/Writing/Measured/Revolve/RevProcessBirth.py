from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart


# process id plus creation file time distinguish actual exact build independent native lifetimes
def RevProcessBirth(Record: dict[str, object]) -> tuple[int, int]:
    Identity = ReadMeasMap(Record.get("oracle_identity"))
    ProcessId = Identity.get("process_id")
    BirthTime = Identity.get("process_creation_filetime")
    if (
        Identity.get("file_version") != KOraclePart["build"]
        or Identity.get("sha256") != KOraclePart["sha256"]
        or Identity.get("version_matches") is not True
        or Identity.get("pe_machine") != "0x8664"
        or type(ProcessId) is not int
        or ProcessId <= 0
        or type(BirthTime) is not int
        or BirthTime <= 0
    ):
        raise ValueError("measured revolve needs the registered exact-build oracle")
    return ProcessId, BirthTime
