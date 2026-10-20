# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

import hashlib as HashCodec
from typing import TYPE_CHECKING as TypeChecking

from interchange.payloads.PayloadRoles import PayloadRole

if TypeChecking:
    from interchange.document.models.DocumentModel import CadDocument


# source recovery needs unambiguous document and digest binding payload indexes
def GetPayloadIds(DocumentValue: CadDocument) -> frozenset[int]:
    try:
        SourceDigest = bytes.fromhex(DocumentValue.Source.SourceDigest)
    except ValueError:
        return frozenset()
    if len(SourceDigest) != HashCodec.sha256().digest_size:
        return frozenset()
    SourceDigestText = DocumentValue.Source.SourceDigest.casefold()
    DocumentIndexes = tuple(
        IndexValue
        for IndexValue, PayloadValue in enumerate(DocumentValue.BrepPayloads)
        if PayloadValue.ValueRole == PayloadRole.KDocument
        and (
            HashCodec.sha256(PayloadValue.PayloadData).hexdigest()
            if PayloadValue.PayloadData is not None
            else PayloadValue.SourceDigest.casefold()
        )
        == SourceDigestText
    )
    BindingIndexes = tuple(
        IndexValue
        for IndexValue, PayloadValue in enumerate(DocumentValue.BrepPayloads)
        if PayloadValue.ValueRole in (PayloadRole.KVerification, PayloadRole.KDocument)
        and PayloadValue.PayloadData == SourceDigest
        and PayloadValue.SourceDigest.casefold()
        == HashCodec.sha256(SourceDigest).hexdigest()
    )
    if len(DocumentIndexes) != 1 or len(BindingIndexes) != 1:
        return frozenset()
    return frozenset((*DocumentIndexes, *BindingIndexes))
