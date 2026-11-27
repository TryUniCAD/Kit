# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from io import BytesIO as ByteStream

from pytest import raises as RaisesError

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.freecad.Adapter import (
    FreeCadAdapter,
    RebuildResult,
    ResolveTarget,
    TrustedNative,
)
from convert.adapters.freecad.Replay.NativeOuter import NativeOuter
from convert.adapters.freecad.Replay.PrepareReplay import PrepareReplay
from convert.adapters.freecad.Replay.ReadCache import KReplayReadCache
from interchange.document.Models.DocumentModel import CadDocument


# retained codec checks require separate evidence that public exports reject the same unqualified history
def CodecRebuild(
    Document: CadDocument, Target: KTargetType, Options: WriteOptions | None = None
) -> WriteResult:
    Adapter = FreeCadAdapter()
    GuardOutput = ByteStream(b"existing destination")
    with RaisesError(
        ValueError, match="native-only|native or unresolved|required features"
    ):
        _ = Adapter.write(Document, GuardOutput, WriteOptions(values={"rebuild": True}))
    assert GuardOutput.getvalue() == b"existing destination"
    Selected = Options or WriteOptions()
    ReplayReads: KReplayReadCache = {}
    Prepared, NativeSource = PrepareReplay(
        Document, Migrate=True, ReplayReads=ReplayReads
    )
    return RebuildResult(
        Adapter,
        Prepared,
        Target,
        ResolveTarget(Target),
        Selected,
        Selected.Overwrite,
        Selected.OptionValues.get("portable", True) is True,
        NativeOuter(Prepared),
        TrustedNative(Document, NativeSource, ReplayReads),
        ReplayReads,
    )
