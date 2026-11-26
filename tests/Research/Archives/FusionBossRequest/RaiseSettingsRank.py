# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as ReplaceValue

from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel

from tests.Research.Archives.FusionBossRequest.ReplaceSubjects import ReplaceSubjects


# a wrong width rank must be refused even when the owner and target are correct
def RaiseRank(Model: DocumentModel, Graph: NativeGraph) -> DocumentModel:
    SketchNode = SelectExtrusion(Graph).Sketch
    Width, _ = LinkedNodes(Graph, SketchNode, "dimensions")
    Subjects = Width.Frame.Subjects
    assert Subjects
    Selected, OtherSubjects = Subjects[0], Subjects[1:]
    Settings = Graph.OneClass("CommonDataAssetSettings")
    assert Graph.Resolve(Selected.Target, Width.SegmentId) == Settings
    assert Selected.ObserverIndex == 2
    return ReplaceSubjects(
        Model,
        {
            (Width.SegmentId, Width.ObjectId): (
                ReplaceValue(Selected, ObserverIndex=4),
                *OtherSubjects,
            ),
        },
    )
