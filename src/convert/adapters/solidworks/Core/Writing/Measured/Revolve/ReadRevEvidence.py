from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import KOraclePart
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.ReadAuthRevJson import (
    ReadAuthRevJson,
)
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.ReadRevReports import (
    ReadRevReports,
)
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.RevEvidence import (
    RevEvidence,
)
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.RevReportPins import (
    KRevReports,
)


# the caller supplies the exact authoring event and the independently authenticated evidence in memory
def ReadRevEvidence(OptionsValue: WriteOptions) -> RevEvidence:
    SourceValue = OptionsValue.values.get(KPartMeasureOpt)
    if SourceValue is None:
        raise ValueError(
            "measured revolve requires an offline native measurement receipt"
        )
    Envelope = ReadMeasMap(SourceValue)
    WrittenAt = Envelope.get("written_at")
    if (
        set(Envelope) != {"written_at", "receipt"}
        or type(WrittenAt) is not int
        or not 0 <= WrittenAt <= 0xFFFFFFFF
    ):
        raise ValueError("measured revolve requires its archive creation epoch")
    Receipt = ReadMeasMap(Envelope["receipt"])
    ReportPins = KRevReports["end_modes"]
    if set(Receipt) == ReportPins.keys():
        Summary, Report, JobValue = (
            ReadAuthRevJson(
                Receipt[ReportKey], Digest, Schema, ReportKey != "generation_receipt"
            )
            for ReportKey, (Digest, Schema) in ReportPins.items()
        )
        if (
            Report.get("job_sha256") != ReportPins["inspection_job"][0]
            or Report.get("build") != KOraclePart["build"]
            or Report.get("passed") is not True
            or any(
                Record.get("generation_receipt_sha256") != ReportPins["generation_receipt"][0]
                or Record.get("writer_revision") != Summary.get("source_revision")
                or Record.get("writer_source_tree") != Summary.get("source_tree")
                or Record.get("spec_sha256") != Summary.get("spec_sha256")
                for Record in (JobValue, Report)
            )
        ):
            raise ValueError(
                "measured revolve requires its passing exact-build inspection"
            )
        return RevEvidence(
            WrittenAt, Summary, Report, JobValue, ReportPins["native_result"][0], True
        )
    Summary, Report, JobValue = ReadRevReports(Receipt)
    return RevEvidence(
        WrittenAt,
        Summary,
        Report,
        JobValue,
        KRevReports["principal"]["native_result"][0],
        False,
    )
