# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Native.Policy.CheckScopes import CheckScopes
from convert.api.ApiOpen import OpenDocument
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from pytest import raises as Raises

from tests.Research.Archives.FusionBossRequest.CheckAnchorWire import CheckAnchorWire


# the typed archive must preserve the emitted roles and the established public refusal
def VerifyBossArc(ArchiveBytes: bytes) -> None:
    Model = ReadDocument(ArchiveBytes)
    Graph = BuildGraph(Model)
    Context = SelectExtrusion(Graph)
    CheckScopes(Graph, Context, Model.Asset.AssetId)
    RulesValue = LinkedNodes(Graph, Context.Sketch, "constraints")
    Dimensions = LinkedNodes(Graph, Context.Sketch, "dimensions")
    assert tuple(RowValue.Fields["constraintType"] for RowValue in RulesValue) == (
        64,
        128,
        64,
        128,
        1,
    )
    assert tuple(RowValue.Fields["constraintType"] for RowValue in Dimensions) == (
        1 << 22,
        1 << 23,
    )
    CheckAnchorWire(Graph, Context.Sketch)
    (BodyValue,) = Model.Bodies
    History = BodyValue.History
    assert isinstance(History, PrismHistory)
    assert (History.Model.Width, History.Model.Depth, History.Model.Height) == (
        40,
        20,
        10,
    )
    assert Context.Extrude.Fields["booleanOperation"] == 4
    with Raises(ValueError, match="Unsupported Fusion user parameter inventory"):
        _ = OpenDocument(ArchiveBytes, SourceFormat="fusion.f3d", StrictMode=True)
