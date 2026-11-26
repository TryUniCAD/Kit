# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes

from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Projection.ProjectPrism import ProjectPrism
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Enums.EnumGeometry import ConstraintKind
from interchange.Records.RecordSource import CadSource


# the actual prism projector can verify semantics before whole archive admission is qualified
def CheckPrismRead(
    Model: DocumentModel, Graph: NativeGraph, ArchiveBytes: bytes
) -> CadDocument:
    Source = CadSource("fusion.f3d", "", HashBytes(ArchiveBytes).hexdigest())
    Document = ProjectPrism(Model, Source, Graph)
    (SketchValue,) = Document.sketches
    assert tuple(Relation.kind for Relation in SketchValue.constraints) == (
        ConstraintKind.KHorizontal,
        ConstraintKind.KVertical,
        ConstraintKind.KHorizontal,
        ConstraintKind.KVertical,
        ConstraintKind.KCoincident,
        ConstraintKind.KDistanceX,
        ConstraintKind.KDistanceY,
    )
    assert Document.feature_timeline[-1].operation == BooleanOp.KCreate
    assert Document.metadata["fusion.read_only"] is True
    return Document
