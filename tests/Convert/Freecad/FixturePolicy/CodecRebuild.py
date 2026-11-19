# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
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
    NativeOuter,
    RebuildResult,
    ResolveTarget,
    TrustedNative,
)
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
    return RebuildResult(
        Adapter,
        Document,
        Target,
        ResolveTarget(Target),
        Selected,
        Selected.Overwrite,
        Selected.OptionValues.get("portable", True) is True,
        NativeOuter(Document),
        TrustedNative(Document),
    )
