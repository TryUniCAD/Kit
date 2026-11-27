from hashlib import sha256 as CalcSha

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart
from convert.adapters.solidworks.Core.Writing.Measured.Thin.ReadThinJson import (
    ReadThinJson,
)
from convert.adapters.solidworks.Core.Writing.Measured.Thin.ThinReportPins import (
    KThinReportPins,
)


# the caller supplies the exact authoring event and the independently authenticated evidence in memory
def ReadThinReports(
    OptionsValue: WriteOptions,
) -> tuple[int, str, dict[str, object], dict[str, object]]:
    SourceValue = OptionsValue.values.get(KPartMeasureOpt)
    if SourceValue is None:
        raise ValueError(
            "SOLIDWORKS thin revolve publication requires an offline native measurement receipt"
        )
    Envelope = ReadMeasMap(SourceValue)
    WrittenAt = Envelope.get("written_at")
    if (
        set(Envelope) != {"written_at", "receipt"}
        or type(WrittenAt) is not int
        or WrittenAt != 1760000000
    ):
        raise ValueError(
            "measured thin revolve requires its exact archive creation epoch"
        )
    RecordsValue = ReadMeasMap(Envelope["receipt"])
    ResultText = RecordsValue.get("native_result")
    if (
        set(RecordsValue) != {"native_result", "inspection_job"}
        or type(ResultText) is not str
        or len(ResultText) > 600_000
    ):
        raise ValueError(
            "measured thin revolve requires the native result and its inspection job"
        )
    ReportId = CalcSha(ResultText.encode("utf-8")).hexdigest()
    PinsValue = KThinReportPins.get(ReportId)
    if PinsValue is None:
        raise ValueError(
            "measured thin revolve requires authenticated offline evidence"
        )
    JobId, JobSchema, ReportSchema, CaseCount = PinsValue
    Report = ReadThinJson(ResultText, ReportId, ReportSchema)
    JobValue = ReadThinJson(RecordsValue["inspection_job"], JobId, JobSchema)
    if (
        Report.get("job_sha256") != JobId
        or Report.get("build_receipt_sha256")
        != ReadMeasMap(JobValue.get("files")).get("BuildReceipt.json")
        or Report.get("oracle_build") != KOraclePart["build"]
        or any(
            Report.get(FieldName) != JobValue.get(FieldName)
            for FieldName in (
                "writer_revision",
                "writer_sdk_tree",
                "source_lock_sha256",
            )
        )
        or any(
            Report.get(FieldName) != 4 * CaseCount + 2
            for FieldName in ("fresh_processes", "distinct_processes")
        )
        or any(
            Report.get(FieldName) is not True
            for FieldName in ("passed", "inputs_unchanged", "idle_after")
        )
        or any(
            ReadMeasMap(Report.get(FieldName)).get("passed") is not True
            for FieldName in ("control-before", "control-after")
        )
    ):
        raise ValueError(
            "measured thin revolve requires its passing exact-build inspection"
        )
    return WrittenAt, ReportId, Report, JobValue
