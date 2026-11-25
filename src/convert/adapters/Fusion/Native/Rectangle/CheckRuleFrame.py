# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import RequireFields
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# original constraint subjects bind the same objects as their semantic operands
def CheckRuleFrame(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    RuleNode: NativeNode,
    Subjects: tuple[NativeNode, ...],
) -> None:
    RequireFields(
        RuleNode, {"ParentNode": LocalRef(Context.Sketch.ObjectId), "isVisible": False}
    )
    Metadata = tuple(
        (Subject.FieldName, Subject.TypeName, Subject.Value)
        for Subject in RuleNode.Frame.Metadata or ()
    )
    Actual = tuple(
        (Graph.Resolve(Subject.Target), Subject.ObserverIndex)
        for Subject in RuleNode.Frame.Subjects or ()
    )
    if Metadata != (
        ("EntityGenesis", "IntrinsicMetaTypeuint64", 2),
    ) or Actual != tuple((NodeValue, 0) for NodeValue in Subjects):
        raise ValueError(
            "Native rectangle rule operands disagree with the authored observer links"
        )
