from __future__ import annotations

from zipfile import BadZipFile

from convert.adapters.freecad.Errors.AdapterError import FreeCadAdapterA
from convert.adapters.freecad.Archive import Validated as ValidatedArchiveMembers
from convert.adapters.freecad.Native import NativeFreeCad, ReadNativeFcstd
from convert.adapters.freecad.Replay.ApplyFlags import ApplyFlags
from convert.adapters.freecad.Replay.ApplySketchFlag import ApplySketchFlag
from convert.adapters.freecad.Replay.NativeDocPair import NativeDocPair
from convert.adapters.freecad.Replay.NativeIdentity import (
    KReplaySemanticAttr,
    KReplaySketchAttr,
)
from convert.adapters.freecad.Replay.PrepareChildren import PrepareChildren
from convert.adapters.freecad.Replay.SemanticDigest import SemanticDigest
from convert.adapters.freecad.Replay.SetReplayDigest import SetReplayDigest
from interchange.Payloads.PayloadRecord import BrepPayload
from interchange.document.Models.DocumentModel import CadDocument


# each embedded child has its own archive binding and historical digest
def PrepareChild(DocValue: CadDocument) -> CadDocument:
    return PrepareReplay(DocValue, Migrate=True)[0]


# failed parent verification leaves child verification independent of exact parent replay
def RebuildReplay(
    DocValue: CadDocument,
    NativeDoc: BrepPayload,
    InitialDigest: str,
    Migrate: bool,
    *,
    RetireParent: bool = False,
) -> tuple[CadDocument, None]:
    if not Migrate:
        return DocValue, None
    Prepared = PrepareChildren(DocValue, PrepareChild)
    if RetireParent or SemanticDigest(Prepared) != InitialDigest:
        Prepared = SetReplayDigest(Prepared, NativeDoc, None)
    return Prepared, None


# write requests share archive verification between exact replay and legacy sketch migration
def PrepareReplay(
    DocValue: CadDocument, *, Migrate: bool
) -> tuple[CadDocument, bytes | None]:
    PairValue = NativeDocPair(DocValue)
    if PairValue is None:
        return DocValue, None
    NativeDoc, _ = PairValue
    Expected = NativeDoc.attributes.get(KReplaySemanticAttr)
    DataValue = NativeDoc.data
    if not isinstance(Expected, str) or DataValue is None:
        return DocValue, None
    InitialDigest = SemanticDigest(DocValue)
    IsUnchanged = InitialDigest == Expected
    if not IsUnchanged and not Migrate:
        return DocValue, None
    ReplayBytes = DataValue if IsUnchanged else None
    try:
        Archive, _ = ValidatedArchiveMembers(DataValue)
        Archive.close()
        Current = ReadNativeFcstd(DataValue, DocValue.source.path)
        IsHistorical = KReplaySketchAttr not in NativeDoc.attributes
        if SemanticDigest(Current) == Expected:
            if Migrate and IsHistorical:
                DocValue = SetReplayDigest(DocValue, NativeDoc, Expected)
            return DocValue, ReplayBytes
        if IsHistorical:
            Legacy = ReadNativeFcstd(
                DataValue, DocValue.source.path, LegacyVisibility=True
            )
            if SemanticDigest(Legacy) == Expected:
                if Migrate:
                    DocValue = ApplyFlags(Legacy, Current, DocValue)
                return DocValue, ReplayBytes
            if Migrate:
                return RebuildReplay(
                    ApplySketchFlag(DocValue, Legacy, Current),
                    NativeDoc,
                    InitialDigest,
                    True,
                    RetireParent=True,
                )
    except (NativeFreeCad, FreeCadAdapterA, OSError, TypeError, ValueError, BadZipFile):
        return RebuildReplay(DocValue, NativeDoc, InitialDigest, Migrate)
    return RebuildReplay(DocValue, NativeDoc, InitialDigest, Migrate)
