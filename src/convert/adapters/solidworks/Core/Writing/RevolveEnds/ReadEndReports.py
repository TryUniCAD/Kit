from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import KOraclePart
from convert.adapters.solidworks.Core.Writing.RevolveEnds.ReadRevEndJson import (
    ReadRevEndJson,
)
from convert.adapters.solidworks.Core.Writing.RevolveEnds.RevEndReportPins import (
    KRevEndReportPins,
)
from convert.adapters.solidworks.Core.Writing.RevolveEnds.RevEndReports import (
    RevEndReports,
)


# the exact native result must refer to the matching job and independently frozen generated archive set
def ReadEndReports(Receipt: dict[str, object]) -> RevEndReports:
    if Receipt.keys() != KRevEndReportPins.keys():
        raise ValueError("revolve end receipt requires the generation, result and job")
    Generation, Result, JobValue = (
        ReadRevEndJson(Receipt[KeyValue], SchemaValue, Digests)
        for KeyValue, (SchemaValue, Digests) in KRevEndReportPins.items()
    )
    GenSha = KRevEndReportPins["generation_receipt"][1][0]
    if (
        Result.get("job_sha256") != KRevEndReportPins["inspection_job"][1][0]
        or Result.get("build") != KOraclePart["build"]
        or Result.get("passed") is not True
        or any(
            Record.get("oracle_sha256") != KOraclePart["sha256"]
            or Record.get("generation_receipt_sha256") != GenSha
            or Record.get("writer_revision") != Generation.get("source_revision")
            or Record.get("writer_source_tree") != Generation.get("source_tree")
            or Record.get("spec_sha256") != Generation.get("spec_sha256")
            for Record in (JobValue, Result)
        )
    ):
        raise ValueError("measured revolve ends require passing exact-build evidence")
    return RevEndReports(
        Generation, Result, JobValue, KRevEndReportPins["native_result"][1][0]
    )
