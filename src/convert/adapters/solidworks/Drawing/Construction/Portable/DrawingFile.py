from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Construction.Model.DrawRootGraph import (
    DrawRootGraph,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.BlankGraph import (
    BlankGraph,
)


# candidate construction must retain its actual sdk graph and independently addressable streams alongside the generated container
@DataClass(frozen=True, slots=True)
class DrawingFile:
    ModelGraph: DrawRootGraph
    UiGraph: BlankGraph
    HeaderValue: ArchiveNode
    StreamsValue: Mapping[str, bytes]
    BytesValue: bytes
    SourceSheetId: str
