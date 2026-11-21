from pathlib import Path as FilePath
from sys import getprofile as GetProfile, setprofile as SetProfile
from types import FrameType
from typing import cast as CastValue

from convert import open_document as OpenDocument
from convert.adapters.freecad.Native import ReadNativeFcstd
from convert.adapters.freecad.Replay.AnnotateNative import AnnotateNative
from convert.adapters.freecad.Replay.PrepareChildren import PrepareChildren
from convert.adapters.freecad.Replay.PrepareReplay import PrepareReplay
from convert.adapters.freecad.Replay.ReadCache import KReplayReadCache
from convert.adapters.freecad.Replay.ReplayReadScope import ReplayReadScope
from interchange.document.Models.DocumentModel import CadDocument
from tests.Research.Archives.FreeCadAliases.MakePadFixture import MakePadFixture
from tests.Research.Archives.FreeCadAliases.MakePadParent import MakePadParent
from tests.Research.Archives.FreeCadAliases.PreLinkCarrier import PreLinkCarrier


# replay must learn the earlier pad projection through the actual parent archive and reuse it
def CheckCachedPad(TmpPath: FilePath) -> None:
    Child = TmpPath.resolve() / "Child.FCStd"
    Parent = Child.with_name("Parent.FCStd")
    ChildBytes = MakePadFixture("native")
    ParentBytes = MakePadParent()
    assert Child.write_bytes(ChildBytes) == len(ChildBytes)
    assert Parent.write_bytes(ParentBytes) == len(ParentBytes)
    Opened = OpenDocument(Parent, source_format="freecad.fcstd")
    Carried = AnnotateNative(PrepareChildren(Opened, PreLinkCarrier))
    Cache: KReplayReadCache = {}
    Calls: list[tuple[str, int]] = []
    CacheHits: list[tuple[str, bool]] = []

    # native archive entry and depth distinguish parent decoding from a standalone retry
    def RecordRead(Frame: FrameType, Event: str, ArgValue: object) -> None:
        if Event == "call" and Frame.f_code is ReadNativeFcstd.__code__:
            PathValue = CastValue(str, Frame.f_locals["SourcePath"])
            Depth = CastValue(int, Frame.f_locals["OuterDepth"])
            Calls.append((PathValue, Depth))
        if (
            Event == "return"
            and Frame.f_code is ReplayReadScope.FindRead.__code__
            and isinstance(ArgValue, CadDocument)
        ):
            ScopeValue = CastValue(ReplayReadScope, Frame.f_locals["self"])
            CacheHits.append((ArgValue.source.path, ScopeValue.LegacyPadExpr))

    Previous = GetProfile()
    try:
        SetProfile(RecordRead)
        Prepared, Output = PrepareReplay(Carried, Migrate=True, ReplayReads=Cache)
    finally:
        SetProfile(Previous)
    assert Calls == [(str(Parent), 0), (str(Child), 1)] * 2
    assert CacheHits == [(str(Child), True)]
    assert Prepared == Carried and Output == ParentBytes
