# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields, SeriesItems
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph


# snapshot ownership must stay reciprocal across history cache geometry and sketch roles
def CheckSnapOwners(
    Graph: NativeGraph, Context: ExtrudeContext, AssetId: str, Member: str
) -> tuple[object, ...]:
    Component = Context.Component
    Bodies = ResolveField(Graph, Component, "rBodies", "Bodies")
    Cache = ResolveField(Graph, Component, "rCacheBodies", "Bodies")
    History = ResolveField(Graph, Bodies, "rBRepSerializer", "BRepHistorySerializer")
    Serializer = ResolveField(Graph, Cache, "rBRepSerializer", "BRepSerializer")
    assert (
        Bodies != Cache and ResolveField(Graph, History, "rBodies", "Bodies") == Bodies
    )
    assert ResolveField(Graph, Serializer, "rBodies", "Bodies") == Cache
    assert Member == "Breps.BlobParts/" + str(Serializer.Fields["partName"])
    IdGen = ResolveField(
        Graph, Serializer, "topEntityPIDGenerator", "PassiveIdGenerator"
    )
    ToolNode = ResolveField(
        Graph, Context.Extrude, "rExtrudeToolBody", "DcExtrudeToolBody"
    )
    Region = Graph.OneClass("SketchRegionRef")
    (ToolOwner,) = LinkedNodes(Graph, ToolNode, "toolbodyCaches")
    (RegionOwner,) = LinkedNodes(Graph, Region, "caches")
    assert {Owner.Identity for Owner in Graph.ByClass("ETCachedTopology")} == {
        ToolOwner.Identity,
        RegionOwner.Identity,
    }
    for Owner in (ToolOwner, RegionOwner):
        assert Owner.Fields["progenitor"] is None
        assert ObjectFields(Owner.Fields["scope"]) == {
            "assetId": AssetId,
            "scopeEntityIdentifier": Component.Fields["persistentId"],
            "scopeIdType": 2,
            "segmentId": Component.SegmentId,
        }
    Roots = SeriesItems(IdGen.Fields["scanOrderIndex"])
    assert (
        Roots
        == (
            ToolOwner.Fields["cachedEntityId"],
            RegionOwner.Fields["cachedEntityId"],
            Context.Sketch.Fields["bodyId"],
        )
        == (3, 2, 1)
    )
    assert SeriesItems(IdGen.Fields["addressOfTopEntities"]) == (0, 0, 0)
    assert IdGen.Fields["nextId"] == 4
    return Roots
