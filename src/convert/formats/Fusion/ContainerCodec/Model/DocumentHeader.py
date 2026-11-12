from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class DocumentHeader:
    DocumentId: str
    CurrentVersion: str
    SoftwareVersion: int
    Versions: tuple[tuple[str, int], ...]
    AssetId: str
    TypeName: str = "Fusion Document"
    TypeDescription: str = "A Fusion Document"
