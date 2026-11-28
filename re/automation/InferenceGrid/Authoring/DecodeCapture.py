# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from json import loads

from ReaderEvidence import reader_evidence


# fresh native samples must exercise the public reader and retain every unresolved field
def DecodeCapture(Content, Application, NameValue):
    from convert import open_document

    FormatValue = {"fusion": "fusion.f3d", "solidworks": "solidworks.sldprt"}[
        Application
    ]
    try:
        Document = open_document(
            Content,
            source_format=FormatValue,
            strict=Application == "solidworks",
            include_brep=False,
            include_tessellation=False,
        )
        Neutral = Document.to_json(indent=None)
        Repeated = open_document(
            Content,
            source_format=FormatValue,
            strict=Application == "solidworks",
            include_brep=False,
            include_tessellation=False,
        ).to_json(indent=None)
        if Neutral != Repeated:
            raise ValueError("public reader produced different neutral bytes on repeat")
    except (ValueError, TypeError, RuntimeError, NotImplementedError) as ErrorValue:
        return {
            "file": NameValue,
            "source_sha256": sha256(Content).hexdigest(),
            "status": "unsupported",
            "reason": str(ErrorValue)[:2048],
        }, None
    Evidence = reader_evidence(loads(Neutral))
    Issues = sorted(
        {(Entry["path"], Entry["reason"]) for Entry in Evidence["unresolved"]}
    )
    return {
        "file": NameValue,
        "source_sha256": sha256(Content).hexdigest(),
        "neutral_sha256": sha256(Neutral.encode("utf-8")).hexdigest(),
        "status": "unresolved" if Issues else "read",
        "deterministic": True,
        "portable_complete": Evidence["portable_complete"],
        "native_acceptance": Evidence["native_acceptance"],
        "counts": Evidence["counts"],
        "unresolved": [
            {"path": PathValue, "reason": ReasonValue}
            for PathValue, ReasonValue in Issues
        ],
    }, Neutral
