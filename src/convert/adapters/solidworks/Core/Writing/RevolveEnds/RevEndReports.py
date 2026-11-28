from dataclasses import dataclass as DataClass


# the independent generation and inspection roles must remain distinct during receipt validation
@DataClass(frozen=True, slots=True)
class RevEndReports:
    GenerationValue: dict[str, object]
    ResultValue: dict[str, object]
    JobValue: dict[str, object]
    NativeSha: str
