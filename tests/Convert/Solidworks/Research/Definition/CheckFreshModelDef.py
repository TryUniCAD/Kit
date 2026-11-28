from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Definition.DefSettingsCases import (
    DefCases,
)
from tests.Convert.Solidworks.Research.Definition.RunModelDefProcess import (
    RunDefProcess,
)


# independently launched readers must recover the authored definitions after complete sdk emission
def CheckFreshDef() -> list[dict[str, object]]:
    Cases = DefCases()
    Reports = [RunDefProcess([CaseValue])[0] for CaseValue in Cases]
    for Index, (CaseValue, BuiltValue) in enumerate(zip(Cases, Reports, strict=True)):
        assert BuiltValue["passed"] is True and BuiltValue["runtime_input_reads"] == 0
        assert (
            BuiltValue["independent_wire_equal"] is True
            and BuiltValue["journal_schema"] == 0
        )
        (Prepared,) = RunDefProcess(
            [{"mode": "prepare", "version": 19000, "input": BuiltValue["output"]}]
        )
        assert {
            FieldName: Value
            for FieldName, Value in BuiltValue.items()
            if FieldName not in ("independent_wire_equal", "output")
        } == Prepared
        assert Prepared["next_map_index"] == 7 and Prepared["style_count"] == 0
        if CaseValue["kind"] == "part":
            assert Prepared["density_kg_m3"] == CaseValue["density_kg_m3"]
            assert Prepared["document_class"] == "uiPartDoc_c"
        else:
            PreferenceValues = CastValue(dict[str, object], Prepared["save_as_part"])
            assert PreferenceValues["f10"] == (0.0 if Index == 2 else 0.9)
            assert PreferenceValues["f3c"] == -9 - Index
            assert Prepared["document_class"] == "uiAssemblyDoc_c"
    assert len({Value["sha256"] for Value in Reports}) == 4
    assert Reports[0]["bytes"] != Reports[1]["bytes"]
    return Reports
