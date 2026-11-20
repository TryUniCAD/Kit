# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace
from hashlib import sha256 as DigestBytes

from interchange.document.Models.DocumentModel import CadDocument
from tests.Research.Archives.FreeCadReplay.ChangeArchive import ChangeArchive


# exact replay must reject changed semantics or broken native source bindings
def ChangeReplay(Document: CadDocument, CaseName: str) -> CadDocument:
    if CaseName == "source-bytes":
        return ChangeArchive(Document)
    if CaseName == "semantic":
        Parameters = tuple(
            (
                Replace(Param, value=Replace(Param.value, value=12.0))
                if Param.attributes.get("freecad_path") == "LengthFwd"
                else Param
            )
            for Param in Document.parameters
        )
        return Replace(Document, parameters=Parameters)
    if CaseName == "fresh":
        return Replace(Document, brep_payloads=())
    Payloads = list(Document.brep_payloads)
    for Index, Payload in enumerate(Payloads):
        if CaseName == "source-hash" and Payload.id == "freecad:native-document":
            Payloads[Index] = Replace(Payload, sha256="0" * 64)
        if CaseName == "binding" and Payload.id == "freecad:native-document-binding":
            DataValue = b"0" * 32
            Payloads[Index] = Replace(
                Payload, data=DataValue, sha256=DigestBytes(DataValue).hexdigest()
            )
        if CaseName == "snapshot" and Payload.id == "freecad:native-document":
            Payloads[Index] = Replace(
                Payload,
                attributes={
                    **Payload.attributes,
                    "freecad.replay_semantic_sha256": "0" * 64,
                },
            )
    return Replace(Document, brep_payloads=tuple(Payloads))
