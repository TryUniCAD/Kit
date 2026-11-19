from __future__ import annotations

from zipfile import BadZipFile

from convert.adapters.freecad.Archive import validated_archive_members
from convert.adapters.freecad.Native import NativeFreeCad, ReadNativeFcstd
from convert.adapters.freecad.Replay.ApplyFlags import ApplyFlags
from interchange.document.Models.DocumentModel import CadDocument


# write requests share archive verification between exact replay and legacy sketch migration
def PrepareReplay(
    DocValue: CadDocument, *, Migrate: bool
) -> tuple[CadDocument, bytes | None]:
    from convert.adapters.freecad.Adapter import (
        FreeCadAdapterA,
        KReplaySemanticAttr,
        NativeDocPair,
        SemanticDigest,
    )

    PairValue = NativeDocPair(DocValue)
    if PairValue is None:
        return DocValue, None
    NativeDoc, _ = PairValue
    Expected = NativeDoc.attributes.get(KReplaySemanticAttr)
    DataValue = NativeDoc.data
    if not isinstance(Expected, str) or DataValue is None:
        return DocValue, None
    IsUnchanged = SemanticDigest(DocValue) == Expected
    if not IsUnchanged and not Migrate:
        return DocValue, None
    ReplayBytes = DataValue if IsUnchanged else None
    try:
        Archive, _ = validated_archive_members(DataValue)
        Archive.close()
        Current = ReadNativeFcstd(DataValue, DocValue.source.path)
        if SemanticDigest(Current) == Expected:
            return DocValue, ReplayBytes
        Legacy = ReadNativeFcstd(DataValue, DocValue.source.path, LegacyVisibility=True)
        if SemanticDigest(Legacy) != Expected:
            return DocValue, None
        if Migrate:
            DocValue = ApplyFlags(DocValue, Legacy, Current)
    except (NativeFreeCad, FreeCadAdapterA, OSError, TypeError, ValueError, BadZipFile):
        return DocValue, None
    return DocValue, ReplayBytes
