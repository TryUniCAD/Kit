# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes

from convert.api.ApiOpen import OpenDocument
from interchange.document.Models.DocumentModel import CadDocument


# strict public readback must retain the same saved graph and explicit read only state
def VerifyPubBoss(ArchiveBytes: bytes, Projected: CadDocument) -> dict[str, object]:
    Public = OpenDocument(ArchiveBytes, SourceFormat="fusion.f3d", StrictMode=True)
    Serialized = Public.to_json()
    assert Serialized == Projected.to_json()
    assert Public.metadata["fusion.read_only"] is True
    assert CadDocument.from_json(Serialized).to_json() == Serialized
    State = Public.metadata["fusion.native_state"]
    assert isinstance(State, dict) and State["version"] == 2
    return {
        "status": "returned_document",
        "native_state_version": 2,
        "read_only": True,
        "document_sha256": HashBytes(Serialized.encode()).hexdigest(),
    }
