# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as ReplaceValue

from interchange.document.Models.DocumentModel import CadDocument
from tests.CliResearch.Comparison.UnifiedDocument import UnifiedDocument
from tests.Convert.Commands.Feature.BuildPlaneHist import BuildPlaneHist


# reference only and suppressed generators must remain observable without producing unified model copies
def MakeIneligible(RecordKind: str) -> CadDocument:
    if RecordKind == "DatumOnly":
        return BuildPlaneHist("Active")
    Document = UnifiedDocument("inactive")
    return ReplaceValue(
        Document,
        feature_timeline=(
            *Document.feature_timeline[:-1],
            ReplaceValue(Document.feature_timeline[-1], suppressed=True),
        ),
    )
