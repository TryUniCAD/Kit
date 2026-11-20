from dataclasses import dataclass as DataClass


# archive and kernel writers must bind the same generated activation and selected mark identities
@DataClass(frozen=True, slots=True)
class ImportHistory:
    BytesValue: bytes
    MarkIds: tuple[int, int]
