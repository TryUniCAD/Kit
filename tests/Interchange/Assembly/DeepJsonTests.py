# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as ReplaceValue
from sys import version_info as KVersionInfo

from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Models.DocumentModel import ComponentDoc
from tests.Interchange.Fixtures.AssemblyFixture import BuildAssembly
from tests.Interchange.Fixtures.AssemblyFixture import BuildPiston


# saved assemblies must reopen across the nesting range supported before decoder optimization
def CheckDeepJson() -> None:
    SourceDoc = BuildPiston()
    Template = BuildAssembly()
    Assembly = Template.assembly
    assert Assembly is not None
    Assembly = ReplaceValue(
        Assembly,
        definitions=tuple(
            ReplaceValue(Definition, body_ids=()) for Definition in Assembly.definitions
        ),
    )
    DepthCount = 80 if KVersionInfo < (3, 12) else 100
    for Index in range(DepthCount):
        SourceDoc = ReplaceValue(
            Template,
            source=ReplaceValue(Template.source, path=f"assembly-{Index}"),
            assembly=ReplaceValue(
                Assembly, documents=(ComponentDoc("document:part", SourceDoc),)
            ),
        )
    SourceDoc.assert_valid()
    Encoded = SourceDoc.to_json(indent=None)
    Restored = CadDocument.from_json(Encoded)
    assert Restored.to_json(indent=None) == Encoded
    for Index in range(DepthCount):
        assert Restored.source.path == f"assembly-{DepthCount - Index - 1}"
        Nested = Restored.assembly
        assert Nested is not None
        Restored = Nested.documents[0].document
    assert Restored == BuildPiston()
