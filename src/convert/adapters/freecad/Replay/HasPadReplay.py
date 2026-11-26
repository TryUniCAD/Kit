from convert.adapters.freecad.Native import ReadNativeFcstd
from convert.adapters.freecad.Replay.NativeIdentity import KExplicitSketchProfile
from convert.adapters.freecad.Replay.ReadCache import KReplayReadCache
from convert.adapters.freecad.Replay.SemanticDigest import SemanticDigest


# marked carriers require independent evidence before replaying an older expression projection
def HasPadReplay(
    DataValue: bytes,
    SourcePath: str,
    Expected: str,
    SketchProfile: object,
    ReplayReads: KReplayReadCache,
) -> bool:
    if SketchProfile != KExplicitSketchProfile:
        return False
    BeforePadLinks = ReadNativeFcstd(
        DataValue,
        SourcePath,
        LegacyPadExpr=True,
        ReplayReads=ReplayReads,
    )
    return SemanticDigest(BeforePadLinks) == Expected
