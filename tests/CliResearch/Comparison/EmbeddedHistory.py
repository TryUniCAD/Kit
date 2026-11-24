# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as ReplaceValue

from interchange.assembly.AssemblyEnums import ComponentKind
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.document.Models.DocumentModel import AssemblyData
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Models.DocumentModel import ComponentDoc
from tests.Research.Archives.Comparison.SemanticDocuments import MakeDocument


# nested inputs must isolate missing component history from an otherwise populated root history
def MakeEmbedded(HasHistory: bool) -> CadDocument:
    Nested = MakeDocument("child")
    if not HasHistory:
        Nested = ReplaceValue(
            Nested,
            parameters=(ReplaceValue(Nested.parameters[0], owner_id=""),),
            support_planes=(),
            sketches=(),
            selections=(),
            feature_timeline=(),
            bodies=(),
        )
    return ReplaceValue(
        MakeDocument("root"),
        assembly=AssemblyData(
            "assemblyroot",
            (ComponentDef("assemblyroot", "Root", ComponentKind.KAssembly),),
            (),
            documents=(ComponentDoc("embeddedpart", Nested),),
        ),
    )
