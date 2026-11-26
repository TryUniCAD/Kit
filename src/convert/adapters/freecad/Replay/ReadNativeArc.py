from __future__ import annotations

from collections.abc import Callable
from pathlib import Path as FilePath

from convert.adapters.freecad.NativeParameters.RecoverAlias import RecoverAlias
from convert.adapters.freecad.Replay.AnnotateNative import AnnotateNative
from convert.adapters.freecad.Replay.OuterState import OuterState
from convert.adapters.freecad.Replay.ReadCache import KReplayReadCache
from convert.adapters.freecad.Replay.ReplayReadScope import ReplayReadScope
from interchange.document.Models.DocumentModel import CadDocument


# outer reads carry limits and replay context independently of native model decoding
def ReadNativeArc(
    DataValue: bytes,
    SourcePath: str,
    SourceFile: FilePath | None,
    StateValue: OuterState | None,
    OuterDepth: int,
    LegacyVisibility: bool,
    LegacyPadExpr: bool,
    RecordReplay: bool,
    ReplayReads: KReplayReadCache | None,
    DecodeDoc: Callable[
        [bytes, str, OuterState | None, int, bool, bool],
        tuple[CadDocument, tuple[CadDocument, ...], bool],
    ],
) -> CadDocument:
    ActiveState = StateValue
    ReadScope = (
        ReplayReadScope(
            ReplayReads,
            SourceFile.parent if SourceFile is not None else None,
            LegacyVisibility,
            LegacyPadExpr,
        )
        if StateValue is None and ReplayReads is not None and not RecordReplay
        else None
    )
    if ActiveState is None and SourceFile is not None:
        ActiveState = OuterState(
            SourceFile.parent,
            {},
            {SourceFile},
            1,
            len(DataValue),
            LegacyVisibility,
            RecordReplay,
            ReadScope,
            LegacyPadExpr,
        )
    if ActiveState is not None:
        LegacyVisibility = ActiveState.LegacyVisibility
        LegacyPadExpr = ActiveState.LegacyPadExpr
        RecordReplay = ActiveState.RecordReplay
        ReadScope = ActiveState.ReplayScope
    IsNested = StateValue is not None or OuterDepth != 0
    InitialReuse = ReadScope.ReusedReads if ReadScope is not None else 0
    if ReadScope is not None and not IsNested:
        Cached = ReadScope.FindRead(SourcePath, DataValue)
        if Cached is not None:
            return Cached
    DocValue, Children, HasUnresolved = DecodeDoc(
        DataValue, SourcePath, ActiveState, OuterDepth, LegacyVisibility, LegacyPadExpr
    )
    DocValue = RecoverAlias(DocValue)
    if RecordReplay and not (LegacyVisibility or LegacyPadExpr):
        return AnnotateNative(DocValue)
    if ReadScope is not None:
        ReadScope.RememberRead(
            DocValue,
            SourceFile,
            Children,
            HasUnresolved=HasUnresolved,
            Nested=IsNested,
            InitialReuse=InitialReuse,
        )
    return DocValue
