from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# field writers must retain mutable mapping formulas and the original graph owner
@DataClass(frozen=True, slots=True)
class WriteFrame:
    WriterValue: BodyWriter
    ScopeValue: FieldScope
    NodeValue: ArchiveNode
    SchemaWriter: Callable[[WriteFrame, str], None]
    FieldsWriter: Callable[[WriteFrame, tuple[NativeField, ...]], None]
