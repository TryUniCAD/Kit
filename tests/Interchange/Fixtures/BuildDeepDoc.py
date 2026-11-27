# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as ReplaceValue

from interchange.assembly.AssemblyData import AssemblyData
from interchange.assembly.AssemblyEnums import ComponentKind
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentDocument import ComponentDoc
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordParameter import Parameter, ParameterValue
from tests.Interchange.Fixtures.DocumentFixture import BuildDocument


# linked document chains expose recursion regressions across the complete public persistence boundary
def BuildDeepDoc(DepthValue: int) -> CadDocument:
    EmptyValue = ReplaceValue(
        BuildDocument(),
        support_planes=(),
        sketches=(),
        feature_timeline=(),
        bodies=(),
        capabilities=frozenset(),
        parameters=(Parameter("depth", "Depth", ParameterValue(1)),),
    )
    InnerValue = EmptyValue
    for IndexValue in range(DepthValue):
        ChildKind = (
            ComponentKind.KAssembly
            if InnerValue.assembly is not None
            else ComponentKind.KPart
        )
        AssemblyValue = AssemblyData(
            "root",
            (
                ComponentDef("root", f"Root{IndexValue}", ComponentKind.KAssembly),
                ComponentDef("child", "Child", ChildKind, document_id="embedded"),
            ),
            (ComponentInst("instance", "Child", "child", "root"),),
            documents=(ComponentDoc("embedded", InnerValue),),
        )
        InnerValue = ReplaceValue(EmptyValue, assembly=AssemblyValue)
    return InnerValue
