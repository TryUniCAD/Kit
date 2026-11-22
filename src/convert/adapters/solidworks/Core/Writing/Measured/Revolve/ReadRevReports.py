from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import KOraclePart
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.ReadAuthRevJson import (
    ReadAuthRevJson,
)
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.RevReportPins import (
    KRevReports,
)


# the actual report must link the inspected job exact executable and complete six process batch
def ReadRevReports(
    Envelope: dict[str, object],
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    if set(Envelope) != KRevReports.keys():
        raise ValueError("measured revolve requires the summary, native result and inspection job")
    Summary, Report, JobValue = (
        ReadAuthRevJson(Envelope[ReportKey], Digest, Schema) for ReportKey, (Digest, Schema) in KRevReports.items()
    )
    if (
        Summary.get("native_report_sha256") != KRevReports["native_result"][0]
        or Summary.get("job_sha256") != KRevReports["inspection_job"][0]
        or Report.get("job_sha256") != KRevReports["inspection_job"][0]
        or any(RowValue.get("source_revision") != JobValue.get("source_revision") for RowValue in (Summary, Report))
        or Summary.get("oracle_version") != KOraclePart["build"]
        or Summary.get("paired_mass_metrics") != 36
        or any(
            RowValue.get("distinct_processes") != 6 or RowValue.get("controls_healthy") is not True
            for RowValue in (Summary, Report)
        )
        or Report.get("passed") is not True
        or Report.get("saved_edit_reopened") is not True
        or JobValue.get("inspect_before_rebuild") is not True
        or JobValue.get("verify_saved_edit") is not True
    ):
        raise ValueError("measured revolve requires its passing exact-build inspection")
    return Summary, Report, JobValue
