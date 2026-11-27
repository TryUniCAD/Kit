# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as ReplaceValue

from interchange.document.Models.DocumentModel import CadDocument
from tests.Research.Archives.Comparison.SemanticDocuments import MakeDocument


# unified positives need a supported active sketch and extrusion history rather than descriptive datum records
def UnifiedDocument(Prefix: str) -> CadDocument:
    Document = MakeDocument(Prefix)
    SketchStep = ReplaceValue(
        Document.feature_timeline[0],
        definition=None,
        sketch_id=Document.sketches[0].id,
    )
    return ReplaceValue(
        Document, feature_timeline=(SketchStep, *Document.feature_timeline[1:])
    )
