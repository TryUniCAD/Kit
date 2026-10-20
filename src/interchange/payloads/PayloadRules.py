# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.payloads.PayloadRoles import PayloadRole
from interchange.payloads.PayloadRuleModel import PayloadRule


# suffix evidence remains explicit because unknown formats still expose useful filenames
KSuffixPayloadRules = (
    PayloadRule(PayloadRole.KBrep, ".brep", SourceSuffixes=frozenset({".brep"})),
    PayloadRule(PayloadRole.KBrep, ".brp", SourceSuffixes=frozenset({".brp"})),
    PayloadRule(PayloadRole.KBrep, ".x_b", SourceSuffixes=frozenset({".x_b"})),
    PayloadRule(PayloadRole.KBrep, ".x_t", SourceSuffixes=frozenset({".x_t"})),
    PayloadRule(PayloadRole.KBrep, ".sat", SourceSuffixes=frozenset({".sat"})),
    PayloadRule(PayloadRole.KBrep, ".sab", SourceSuffixes=frozenset({".sab"})),
    PayloadRule(PayloadRole.KBrep, ".cgm", SourceSuffixes=frozenset({".cgm"})),
    PayloadRule(PayloadRole.KBrep, ".mfbrp", SourceSuffixes=frozenset({".mfbrp"})),
    PayloadRule(PayloadRole.KTessellation, ".cgr", SourceSuffixes=frozenset({".cgr"})),
    PayloadRule(
        PayloadRole.KVerification, ".sha256", SourceSuffixes=frozenset({".sha256"})
    ),
    PayloadRule(PayloadRole.KDocument, ".FCStd", SourceSuffixes=frozenset({".fcstd"})),
    PayloadRule(
        PayloadRole.KDocument, ".sldprt", SourceSuffixes=frozenset({".sldprt"})
    ),
    PayloadRule(
        PayloadRole.KDocument, ".sldasm", SourceSuffixes=frozenset({".sldasm"})
    ),
    PayloadRule(
        PayloadRole.KDocument, ".catpart", SourceSuffixes=frozenset({".catpart"})
    ),
    PayloadRule(
        PayloadRole.KDocument, ".catproduct", SourceSuffixes=frozenset({".catproduct"})
    ),
)


from interchange.payloads.PayloadRuleData import KFormatPayloadRules


# legacy payload recovery needs ordered evidence matching historical output
KLegacyPayloadRules = KFormatPayloadRules + KSuffixPayloadRules
