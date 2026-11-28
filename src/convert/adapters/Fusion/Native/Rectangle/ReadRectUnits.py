# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    RequireFields,
    ResolveField,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import TextValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from interchange.Enums.EnumUnits import UnitSystem


# display units follow the active modeling length choice without changing stored measurements
def ReadRectUnits(Graph: NativeGraph) -> UnitSystem:
    Settings = Graph.OneClass("CommonDataAssetSettings")
    Units = ResolveField(Graph, Settings, "activeUnitSystem", "UnitSystem")
    Lengths = tuple(
        Choice
        for Choice in LinkedNodes(Graph, Units, "children")
        if Choice.ClassName == "UnitSystemChoiceById"
        and Choice.Fields["id"] == "ModelingLength"
    )
    if len(Lengths) != 1:
        raise ValueError(
            "Native constrained rectangle requires one modeling length setting"
        )
    NativeUnit = TextValue(Lengths[0].Fields["unitString"])
    DisplayUnit = {
        "millimeter": UnitSystem.KMillimeter,
        "inch": UnitSystem.KInch,
    }.get(NativeUnit)
    if DisplayUnit is None:
        raise ValueError("Unsupported native Fusion UnitSystemChoiceById.unitString")
    RequireFields(Lengths[0], {"rParent": LocalRef(Units.ObjectId)})
    return DisplayUnit
