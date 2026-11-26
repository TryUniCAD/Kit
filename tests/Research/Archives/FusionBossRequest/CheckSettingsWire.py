# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode


# browser and design observers must resolve one actual settings entity in schedule order
def CheckSettings(Graph: NativeGraph, SketchNode: NativeNode) -> dict[str, object]:
    Settings = Graph.OneClass("CommonDataAssetSettings")
    Browser = (
        Graph.OneClass("DocumentSettingsBrowserEntry", 2),
        Graph.OneClass("PMISettingsBrowserEntry", 2),
    )
    Width, Height = LinkedNodes(Graph, SketchNode, "dimensions")
    RolesValue = ("settings", "pmi_settings", "width_mm", "height_mm")
    RowsValue: list[dict[str, object]] = []
    for RankValue, (RoleValue, NodeValue) in enumerate(
        zip(RolesValue, (*Browser, Width, Height), strict=True)
    ):
        (Observed,) = [
            Subject
            for Subject in NodeValue.Frame.Subjects or ()
            if Graph.Resolve(Subject.Target, NodeValue.SegmentId) == Settings
        ]
        assert Observed.ObserverIndex == RankValue
        RowsValue.append(
            {
                "role": RoleValue,
                "rank": RankValue,
                "class": NodeValue.ClassName,
                "id": NodeValue.Identity,
            }
        )
    return {
        "settings_id": Settings.Identity,
        "browser_observers": RowsValue[:2],
        "dimension_observers": RowsValue[2:],
    }
