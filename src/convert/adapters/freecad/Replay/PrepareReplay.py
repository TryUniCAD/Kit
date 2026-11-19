from __future__ import annotations

from functools import partial as Partial
from zipfile import BadZipFile

from convert.adapters.freecad.Errors.AdapterError import FreeCadAdapterA
from convert.adapters.freecad.Native import NativeFreeCad, ReadNativeFcstd
from convert.adapters.freecad.Replay.ApplyFlags import ApplyFlags
from convert.adapters.freecad.Replay.ApplySketchFlag import ApplySketchFlag
from convert.adapters.freecad.Replay.NativeDocPair import NativeDocPair
from convert.adapters.freecad.Replay.NativeIdentity import (
    KReplaySemanticAttr,
    KReplaySketchAttr,
)
from convert.adapters.freecad.Replay.PrepareChildren import PrepareChildren
from convert.adapters.freecad.Replay.ReadCache import KReplayReadCache
from convert.adapters.freecad.Replay.SemanticDigest import SemanticDigest
from convert.adapters.freecad.Replay.SetReplayDigest import SetReplayDigest
from interchange.Payloads.PayloadRecord import BrepPayload
from interchange.document.Models.DocumentModel import CadDocument


# each embedded child has its own archive binding and historical digest
def PrepareChild(DocValue: CadDocument, ReplayReads: KReplayReadCache) -> CadDocument:
    return PrepareReplay(DocValue, Migrate=True, ReplayReads=ReplayReads)[0]


# an independent child repair invalidates the previous semantic baseline of the parent
def PrepareLinked(
    DocValue: CadDocument,
    InitialDigest: str | None,
    Migrate: bool,
    ReplayReads: KReplayReadCache,
    ReplayBytes: bytes | None = None,
) -> tuple[CadDocument, bytes | None]:
    if not Migrate:
        return DocValue, ReplayBytes
    Prepared = PrepareChildren(DocValue, Partial(PrepareChild, ReplayReads=ReplayReads))
    if InitialDigest is None or SemanticDigest(Prepared) == InitialDigest:
        return Prepared, ReplayBytes
    PairValue = NativeDocPair(Prepared)
    if PairValue is not None:
        Prepared = SetReplayDigest(Prepared, PairValue[0], None)
    return Prepared, None


# write requests share archive verification between exact replay and legacy sketch migration
def PrepareReplay(
    DocValue: CadDocument, *, Migrate: bool, ReplayReads: KReplayReadCache | None = None
) -> tuple[CadDocument, bytes | None]:
    if ReplayReads is None:
        ReplayReads = {}
    PairValue = NativeDocPair(DocValue)
    if PairValue is None:
        return PrepareLinked(DocValue, None, Migrate, ReplayReads)
    return PrepareBound(DocValue, PairValue[0], Migrate, ReplayReads)


# verified archive bindings can compare current and historical sketch interpretations
def PrepareBound(
    DocValue: CadDocument,
    NativeDoc: BrepPayload,
    Migrate: bool,
    ReplayReads: KReplayReadCache,
) -> tuple[CadDocument, bytes | None]:
    Expected = NativeDoc.attributes.get(KReplaySemanticAttr)
    DataValue = NativeDoc.data
    if not isinstance(Expected, str) or DataValue is None:
        return PrepareLinked(DocValue, None, Migrate, ReplayReads)
    InitialDigest = SemanticDigest(DocValue)
    IsUnchanged = InitialDigest == Expected
    if not IsUnchanged and not Migrate:
        return DocValue, None
    ReplayBytes = DataValue if IsUnchanged else None
    try:
        Current = ReadNativeFcstd(
            DataValue, DocValue.source.path, ReplayReads=ReplayReads
        )
        IsHistorical = KReplaySketchAttr not in NativeDoc.attributes
        if SemanticDigest(Current) == Expected:
            return PrepareLinked(
                DocValue, InitialDigest, Migrate, ReplayReads, ReplayBytes
            )
        if IsHistorical:
            Legacy = ReadNativeFcstd(
                DataValue,
                DocValue.source.path,
                LegacyVisibility=True,
                ReplayReads=ReplayReads,
            )
            if SemanticDigest(Legacy) == Expected:
                if not Migrate:
                    return DocValue, ReplayBytes
                Updated = ApplyFlags(Legacy, Current, DocValue)
                return PrepareLinked(
                    Updated, SemanticDigest(Updated), True, ReplayReads, ReplayBytes
                )
            if Migrate:
                return PrepareLinked(
                    ApplySketchFlag(DocValue, Legacy, Current),
                    InitialDigest,
                    True,
                    ReplayReads,
                )
    except (NativeFreeCad, FreeCadAdapterA, OSError, TypeError, ValueError, BadZipFile):
        return PrepareLinked(DocValue, InitialDigest, Migrate, ReplayReads)
    return PrepareLinked(DocValue, InitialDigest, Migrate, ReplayReads)
