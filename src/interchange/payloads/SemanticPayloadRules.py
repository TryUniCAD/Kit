# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.payloads.PayloadRoles import PayloadRole
from interchange.payloads.PayloadRuleModel import PayloadRule


# semantic evidence recovers payload roles when native format tags are incomplete
KSemanticPayloadRules = (
    PayloadRule(
        PayloadRole.KFeatureHistory, ".osmx", Schemas=frozenset({"catprtcont"})
    ),
    PayloadRule(
        PayloadRole.KAssemblyStructure, ".osmx", Schemas=frozenset({"catprodcont"})
    ),
    PayloadRule(PayloadRole.KBrep, ".cgm", Schemas=frozenset({"cgmgeom"})),
    PayloadRule(PayloadRole.KBrep, ".mfbrp", Schemas=frozenset({"catmfbrp"})),
    PayloadRule(PayloadRole.KTessellation, ".cgr", Schemas=frozenset({"catcgrcont"})),
    PayloadRule(
        PayloadRole.KBrep,
        "",
        Kinds=frozenset({"brep", "brep_mode", "brep_topology", "native_brep", "shape"}),
    ),
    PayloadRule(PayloadRole.KBrep, "", Kinds=frozenset({"resolved-assembly"})),
    PayloadRule(
        PayloadRole.KTessellation,
        "",
        Kinds=frozenset({"native_tessellation", "tessellation"}),
    ),
    PayloadRule(
        PayloadRole.KFeatureHistory,
        "",
        Kinds=frozenset({"feature-records", "feature_history", "native_feature_graph"}),
    ),
    PayloadRule(
        PayloadRole.KAssemblyStructure,
        "",
        Kinds=frozenset({"assembly_structure", "mate-list", "native_product_graph"}),
    ),
    PayloadRule(PayloadRole.KDocument, "", Kinds=frozenset({"native_document"})),
)
