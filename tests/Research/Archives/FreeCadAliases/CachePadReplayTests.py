from pathlib import Path as FilePath
from sys import getprofile as GetProfile, setprofile as SetProfile
from types import FrameType

from convert import open_document as OpenDocument
from convert.adapters.freecad.Native import ReadNativeFcstd
from convert.adapters.freecad.Replay.PrepareReplay import PrepareReplay
from convert.adapters.freecad.Replay.ReadCache import KReplayReadCache
from tests.Research.Archives.FreeCadAliases.MakePadFixture import MakePadFixture
from tests.Research.Archives.FreeCadAliases.PreLinkCarrier import PreLinkCarrier


# replay needs the complete verified earlier projection without reopening its scoped archive
def CheckCachedPad(TmpPath: FilePath) -> None:
    SourcePath = TmpPath / "Source.FCStd"
    Original = MakePadFixture("native")
    assert SourcePath.write_bytes(Original) == len(Original)
    Carried = PreLinkCarrier(OpenDocument(SourcePath, source_format="freecad.fcstd"))
    Cache: KReplayReadCache = {}
    _ = ReadNativeFcstd(
        Original, str(SourcePath), LegacyPadExpr=True, ReplayReads=Cache
    )
    assert len(Cache) == 1
    Calls: list[str] = []

    # recording the production code object distinguishes the shortcut from a fresh archive read
    def RecordRead(Frame: FrameType, Event: str, ArgValue: object) -> None:
        if Event == "call" and Frame.f_code is ReadNativeFcstd.__code__:
            Calls.append(Event)

    Previous = GetProfile()
    try:
        SetProfile(RecordRead)
        Prepared, Output = PrepareReplay(Carried, Migrate=True, ReplayReads=Cache)
    finally:
        SetProfile(Previous)
    assert not Calls
    assert Prepared == Carried and Output == Original
