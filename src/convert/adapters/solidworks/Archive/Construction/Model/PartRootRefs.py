from collections.abc import MutableMapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# model construction must retain actual generated style units and view graphs rather than synthesize missing document intent
@DataClass(frozen=True, slots=True)
class PartRootRefs:
    DetailFields: MutableMapping[str, object]
    DocumentUnits: ArchiveNode
    AnalysisUnits: ArchiveNode
    VisualValue: ArchiveNode
    ViewValues: tuple[ArchiveNode, ...]
