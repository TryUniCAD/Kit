from hashlib import sha256 as CalcSha
from json import dumps as DumpJson, loads as LoadJson

from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap


# derive the published proof digest and checked values from the same private json snapshot
def SnapshotReport(
    Report: dict[str, object],
) -> tuple[dict[str, object], str]:
    Encoded = (
        DumpJson(Report, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")
    return ReadMeasMap(LoadJson(Encoded)), CalcSha(Encoded).hexdigest()
