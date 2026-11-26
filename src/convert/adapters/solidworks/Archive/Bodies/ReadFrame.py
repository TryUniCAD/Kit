from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader


# field readers need the same owner identity through embedded and inherited schemas
@DataClass(frozen=True, slots=True)
class ReadFrame:
    ContextValue: BodyContext
    ReaderValue: GraphReader
    ScopeValue: FieldScope
    NodeValue: ArchiveNode
    SchemaReader: Callable[[ReadFrame, str], None]
    FieldsReader: Callable[[ReadFrame, tuple[NativeField, ...]], None]
