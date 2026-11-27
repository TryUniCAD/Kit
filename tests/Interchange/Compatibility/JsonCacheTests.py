# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from cProfile import Profile as RunProfile
from dataclasses import replace as ReplaceValue
from types import CodeType

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordParameter import Parameter, ParameterValue
from tests.Interchange.Fixtures.DocumentFixture import BuildDocument


# a complete public json roundtrip must resolve repeated record layouts without changing persisted data
def CheckJsonCache() -> None:
    SourceValue = ReplaceValue(
        BuildDocument(),
        parameters=tuple(
            Parameter(f"parameter:{Index}", f"Length{Index}", ParameterValue(Index))
            for Index in range(300)
        ),
    )
    SourceText = SourceValue.to_json(indent=None)
    Profiler = RunProfile()
    RestoredValue = Profiler.runcall(CadDocument.from_json, SourceText)
    HintCalls = sum(
        EntryValue.callcount
        for EntryValue in Profiler.getstats()
        if isinstance(EntryValue.code, CodeType)
        and EntryValue.code.co_name == "get_type_hints"
    )
    assert RestoredValue == SourceValue
    assert RestoredValue.to_json(indent=None) == SourceText
    assert HintCalls < 100
