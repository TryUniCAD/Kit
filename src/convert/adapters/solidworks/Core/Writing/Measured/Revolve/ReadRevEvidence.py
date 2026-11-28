from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.ReadRevReports import (
    ReadRevReports,
)
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.RevEvidence import (
    RevEvidence,
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
    Summary, Report, JobValue = ReadRevReports(ReadMeasMap(Envelope["receipt"]))
    return RevEvidence(WrittenAt, Summary, Report, JobValue)
