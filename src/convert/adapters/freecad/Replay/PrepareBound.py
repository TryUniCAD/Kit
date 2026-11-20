from __future__ import annotations

from collections.abc import Callable
from zipfile import BadZipFile

from convert.adapters.freecad.Errors.AdapterError import FreeCadAdapterA
from convert.adapters.freecad.Native import NativeFreeCad, ReadNativeFcstd
from convert.adapters.freecad.Replay.ApplyFlags import ApplyFlags
from convert.adapters.freecad.Replay.ApplySketchFlag import ApplySketchFlag
from convert.adapters.freecad.Replay.NativeIdentity import (
    KReplaySemanticAttr,
    KReplaySketchAttr,
)
from convert.adapters.freecad.Replay.PrepareLinked import PrepareLinked
from convert.adapters.freecad.Replay.ReadCache import KReplayReadCache
from convert.adapters.freecad.Replay.SemanticDigest import SemanticDigest
from interchange.Payloads.PayloadRecord import BrepPayload
from interchange.document.Models.DocumentModel import CadDocument


# verified archive bindings can compare current and historical sketch interpretations
def PrepareBound(
    DocValue: CadDocument,
    NativeDoc: BrepPayload,
    ReplayReads: KReplayReadCache,
    PrepareBranch: Callable[[CadDocument], CadDocument] | None,
) -> tuple[CadDocument, bytes | None]:
    Expected = NativeDoc.attributes.get(KReplaySemanticAttr)
    DataValue = NativeDoc.data
    if not isinstance(Expected, str) or DataValue is None:
        return PrepareLinked(DocValue, None, PrepareBranch)
    InitialDigest = SemanticDigest(DocValue)
    IsUnchanged = InitialDigest == Expected
    if not IsUnchanged and PrepareBranch is None:
        return DocValue, None
    ReplayBytes = DataValue if IsUnchanged else None
    try:
        Current = ReadNativeFcstd(
            DataValue, DocValue.source.path, ReplayReads=ReplayReads
        )
        IsHistorical = KReplaySketchAttr not in NativeDoc.attributes
        if SemanticDigest(Current) == Expected:
            return PrepareLinked(DocValue, InitialDigest, PrepareBranch, ReplayBytes)
        if IsHistorical:
            Legacy = ReadNativeFcstd(
                DataValue,
                DocValue.source.path,
                LegacyVisibility=True,
                ReplayReads=ReplayReads,
            )
            if SemanticDigest(Legacy) == Expected:
                if PrepareBranch is None:
                    return DocValue, ReplayBytes
                Updated = ApplyFlags(Legacy, Current, DocValue)
                return PrepareLinked(
                    Updated, SemanticDigest(Updated), PrepareBranch, ReplayBytes
                )
            if PrepareBranch is not None:
                return PrepareLinked(
                    ApplySketchFlag(DocValue, Legacy, Current),
                    InitialDigest,
                    PrepareBranch,
                )
    except (NativeFreeCad, FreeCadAdapterA, OSError, TypeError, ValueError, BadZipFile):
        return PrepareLinked(DocValue, InitialDigest, PrepareBranch)
    return PrepareLinked(DocValue, InitialDigest, PrepareBranch)
