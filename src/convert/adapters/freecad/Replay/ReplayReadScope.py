from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass as Dataclass, field as Field
import hashlib as Hashlib
from pathlib import Path as FilePath

from convert.adapters.freecad.Replay.ReadCache import KReplayReadCache
from interchange.document.Models.DocumentModel import CadDocument


# one decode tracks relative source bounds and any earlier cached sibling reads
@Dataclass(slots=True)
class ReplayReadScope:
    Reads: KReplayReadCache
    Root: FilePath | None
    LegacyVisibility: bool
    ReusedReads: int = 0
    Incomplete: set[int] = Field(default_factory=set[int])

    # only an independent validation may reuse a complete projection from this write
    def FindRead(self, SourcePath: str, DataValue: bytes) -> CadDocument | None:
        Digest = Hashlib.sha256(DataValue).hexdigest()
        return self.Reads.get((self.Root, SourcePath, Digest, self.LegacyVisibility))

    # promotion needs a complete subtree free of context inherited from cached siblings
    def RememberRead(
        self,
        Document: CadDocument,
        SourceFile: FilePath | None,
        Children: Iterable[CadDocument],
        *,
        HasUnresolved: bool,
        Nested: bool,
        InitialReuse: int,
    ) -> None:
        if HasUnresolved or any(id(Child) in self.Incomplete for Child in Children):
            self.Incomplete.add(id(Document))
            return
        if Nested and (
            SourceFile is None
            or self.Root != SourceFile.parent
            or InitialReuse != self.ReusedReads
        ):
            return
        Source = Document.source
        self.Reads[(self.Root, Source.path, Source.sha256, self.LegacyVisibility)] = (
            Document
        )
