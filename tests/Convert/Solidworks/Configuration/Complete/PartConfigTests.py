from typing import cast as CastValue

from tests.Convert.Solidworks.Configuration.Complete.RunPartConfig import RunPartConfig

# independent native inputs span different section lengths and shared map growth
KPartCases = (
    (
        "ladder",
        3052,
        25390,
        110,
        2435,
        "e7e700d5b112e7d9d1b1297bac8149707e67d9aac2e3c6f890b4cb2f97b1e5b2",
    ),
    (
        "concave",
        2105,
        22700,
        94,
        1722,
        "f8b42cb72d75f14be04410c18daae6f77164e2561dd5e99d7f26a107b5b049a1",
    ),
)


# complete configuration claims require the entire stream and the actual owning alias
def TestConfigGraph() -> None:
    for CaseName, LightEnd, EndValue, CounterValue, OwnerOffset, WireHash in KPartCases:
        Result = RunPartConfig(CaseName)
        assert Result["lightweight"] == [18, LightEnd]
        assert Result["resolved"] == [LightEnd + 4, EndValue]
        assert Result["bytes"] == EndValue
        assert Result["map_base"] == 4 and Result["map_counter"] == CounterValue
        assert Result["all_map_slots_preserved"] is True
        assert Result["unit_owner"] == [OwnerOffset, OwnerOffset + 2, 2]
        assert Result["exact_replay"] is True and Result["config_sha256"] == WireHash
        Refusals = CastValue(dict[str, str], Result["refusals"])
        assert "no complete unsigned short" in Refusals["one_byte"]
        assert "section exceeds its remaining stream" in Refusals["truncated_resolved"]
        assert "1 trailing bytes" in Refusals["trailing_bytes"]
        assert "differs from its enclosing part" in Refusals["wrong_unit_owner"]
        assert "differs from its enclosing part" in Refusals["wrong_writer_owner"]
