from dataclasses import dataclass as DataClass

from interchange.document.Models.DocumentModel import CadDocument


# retaining the complete original prevents a supported solid subset from silently standing in for source conversion
@DataClass(frozen=True, slots=True)
class ThruSourceEnv:
    DocumentValue: CadDocument
    UnmappedPaths: tuple[str, ...]
