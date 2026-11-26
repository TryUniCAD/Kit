from convert.adapters.freecad.Native import ReadNativeFcstd, ResolvedSource
from convert.adapters.freecad.Replay.ReadCache import KReplayReadCache
from convert.adapters.freecad.Replay.ReplayReadScope import ReplayReadScope
from convert.adapters.freecad.Replay.SemanticDigest import SemanticDigest
from interchange.document.Models.DocumentModel import CadDocument


# complete earlier parses can satisfy linked replay before opening the same referenced subtree again
def ReadReplayGraph(
    DataValue: bytes,
    SourcePath: str,
    Expected: str,
    IsHistorical: bool,
    ReusePad: bool,
    ReplayReads: KReplayReadCache,
) -> tuple[CadDocument, str]:
    if ReusePad and ReplayReads:
        SourceFile = ResolvedSource(SourcePath)
        RootValue = SourceFile.parent if SourceFile is not None else None
        ScopeValue = ReplayReadScope(ReplayReads, RootValue, False, True)
        Cached = ScopeValue.FindRead(SourcePath, DataValue)
        if Cached is not None:
            CachedDigest = SemanticDigest(Cached)
            if CachedDigest == Expected:
                return Cached, CachedDigest
    Current = ReadNativeFcstd(
        DataValue, SourcePath, LegacyPadExpr=IsHistorical, ReplayReads=ReplayReads
    )
    return Current, SemanticDigest(Current)
