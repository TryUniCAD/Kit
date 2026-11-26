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
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

from tests.Research.Archives.FusionBossRequest.BossArcProof import BossArcProof
from tests.Research.Archives.FusionBossRequest.CheckAnchorWire import CheckAnchorWire
from tests.Research.Archives.FusionBossRequest.CheckLineNormals import CheckLineNormal
from tests.Research.Archives.FusionBossRequest.CheckSettingsWire import CheckSettings
from tests.Research.Archives.FusionBossRequest.CheckPrismRead import CheckPrismRead
from tests.Research.Archives.FusionBossRequest.VerifySnapshot import VerifySnapshot
from tests.Research.Archives.FusionBossRequest.VerifyPublicBoss import VerifyPubBoss


# the typed and public readers must preserve the generated topology and read only boundary
def VerifyBossArc(ArchiveBytes: bytes) -> BossArcProof:
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
    CheckLineNormal(Graph, Context.Sketch)
    (BodyValue,) = Model.Bodies
    History = BodyValue.History
    assert isinstance(History, PrismHistory)
    assert (History.Model.Width, History.Model.Depth, History.Model.Height) == (
        40,
        20,
        10,
    )
    assert Context.Extrude.Fields["booleanOperation"] == 4
    return BossArcProof(
        CheckSettings(Graph, Context.Sketch),
        VerifySnapshot(ArchiveBytes, Model, Graph, Context),
        VerifyPubBoss(ArchiveBytes, CheckPrismRead(Model, Graph, ArchiveBytes)),
    )
