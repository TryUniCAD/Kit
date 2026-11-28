# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.Scope.ScopeDocument import KScopeUnresolved
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.GeometryCurves import CircleGeometry


# unrelated histories must retain their established reader until their own grammar is supported
def IsCircleOnly(Document: CadDocument, Model: NativeModel, Stream: str) -> bool:
    if (
        Model.operations
        or Model.cut_source is not None
        or KScopeUnresolved in Model.diagnostics
        or len(Model.sketches) != 1
        or len(Document.sketches) != 1
    ):
        return False
    NativeSketch, Neutral = Model.sketches[0], Document.sketches[0]
    Profiles = tuple(Entity for Entity in Neutral.entities if not Entity.construction)
    return (
        NativeSketch.rectangle is None
        and NativeSketch.native_stream == Stream
        and len(Profiles) == 1
        and isinstance(Profiles[0].geometry, CircleGeometry)
    )
