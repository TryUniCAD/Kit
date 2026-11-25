# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode


# dimension observers bind the shared anchor and independent perimeter point by their original ranks
def CheckDimFrame(
    Graph: NativeGraph,
    Dimension: NativeNode,
    Nodes: tuple[NativeNode, ...],
    Anchor: NativeNode,
    IsWidth: bool,
    Fixed: bool = False,
) -> None:
    Settings = Graph.OneClass("CommonDataAssetSettings")
    Other = Nodes[int(IsWidth)]
    Subjects = tuple(
        (Graph.Resolve(Subject.Target), Subject.ObserverIndex)
        for Subject in Dimension.Frame.Subjects or ()
    )
    Metadata = tuple(
        (Subject.FieldName, Subject.TypeName, Subject.Value)
        for Subject in Dimension.Frame.Metadata or ()
    )
    AnchorRank = int(not IsWidth) + int(not Fixed)
    if (
        len(Subjects) != 3
        or Subjects[0][0] != Settings
        or Subjects[1:] != ((Anchor, AnchorRank), (Other, 0))
        or Metadata != (("EntityGenesis", "IntrinsicMetaTypeuint64", 0),)
    ):
        raise ValueError(
            "Native rectangle dimension observers do not follow the anchored operands"
        )
