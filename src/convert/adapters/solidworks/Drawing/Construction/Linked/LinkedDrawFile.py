from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Construction.Model.DrawRootGraph import (
    DrawRootGraph,
)
from convert.adapters.solidworks.Drawing.Definition.Named.NamedGraph import NamedGraph


# a complete linked result must retain the actual generated child view ownership and source identity mapping alongside its native bytes
@DataClass(frozen=True, slots=True)
class LinkedDrawFile:
    ModelGraph: DrawRootGraph
    UiGraph: NamedGraph
    HeaderValue: ArchiveNode
    ViewValue: ArchiveNode
    ChildValue: PartCandidate
    StreamsValue: Mapping[str, bytes]
    BytesValue: bytes
    SourceSheetId: str
    SourceViewId: str
    SourceRefId: str
