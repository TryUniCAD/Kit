# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel

from tests.Research.Archives.FusionBossRequest.ReplaceSubjects import ReplaceSubjects


# moving an existing subject preserves its target and rank while breaking its role
def MoveObserver(Model: DocumentModel, Graph: NativeGraph) -> DocumentModel:
    Settings = Graph.OneClass("CommonDataAssetSettings")
    Source = Graph.OneClass("DocumentSettingsBrowserEntry", 2)
    Target = Graph.OneClass("NamedViewsBrowserEntry", 2)
    Original = Source.Frame.Subjects or ()
    (Selected,) = [
        Subject
        for Subject in Original
        if Graph.Resolve(Subject.Target, Source.SegmentId) == Settings
    ]
    assert Selected.ObserverIndex == 0
    return ReplaceSubjects(
        Model,
        {
            (Source.SegmentId, Source.ObjectId): tuple(
                Subject for Subject in Original if Subject != Selected
            ),
            (Target.SegmentId, Target.ObjectId): (
                *(Target.Frame.Subjects or ()),
                Selected,
            ),
        },
    )
