# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as ReplaceValue

from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, ResolveField
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef

from tests.Research.Archives.FusionBossRequest.ChangeSnapLink import ChangeSnapLink


# the tool body must refer to its own cache even when a foreign cache has the right type
def RedirectSnap(Model: DocumentModel, Graph: NativeGraph) -> DocumentModel:
    Context = SelectExtrusion(Graph)
    ToolNode = ResolveField(
        Graph, Context.Extrude, "rExtrudeToolBody", "DcExtrudeToolBody"
    )
    Region = Graph.OneClass("SketchRegionRef")
    (ToolOwner,) = LinkedNodes(Graph, ToolNode, "toolbodyCaches")
    (RegionOwner,) = LinkedNodes(Graph, Region, "caches")
    assert ToolOwner.ClassName == RegionOwner.ClassName == "ETCachedTopology"
    assert ToolOwner != RegionOwner
    LinkValue = ValueSeries((LocalRef(RegionOwner.ObjectId),))
    Segments: list[ParsedSegment] = []
    for Segment in Model.Segments:
        if Segment.Metadata.Header.SegmentId != ToolNode.SegmentId:
            Segments.append(Segment)
            continue
        Records: list[EntityRecord] = [
            (
                ChangeSnapLink(Record, LinkValue)
                if Record.ObjectId == ToolNode.ObjectId
                else Record
            )
            for Record in Segment.Records
        ]
        Segments.append(ReplaceValue(Segment, Records=tuple(Records)))
    return ReplaceValue(Model, Segments=tuple(Segments))
