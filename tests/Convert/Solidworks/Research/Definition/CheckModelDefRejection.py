from base64 import b64decode as DecodeBase, b64encode as EncodeBase
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Definition.DefSettingsCases import (
    DefCases,
)
from tests.Convert.Solidworks.Research.Definition.RunModelDefProcess import (
    RunDefProcess,
)


# complete stream admission must reject unsupported revisions and malformed roots before returning a graph
def CheckDefReject(BuiltValue: dict[str, object]) -> None:
    WireData = DecodeBase(CastValue(str, BuiltValue["output"]), validate=True)
    InputValues = (
        WireData[:-1],
        WireData + b"\x00",
        WireData[:20] + bytes(16) + WireData[36:],
    )
    Cases: list[dict[str, object]] = [
        {
            "mode": "prepare",
            "version": 19000,
            "input": EncodeBase(Value).decode("ascii"),
        }
        for Value in InputValues
    ]
    Cases.append({"mode": "prepare", "version": 18000, "input": BuiltValue["output"]})
    PartCase, _, Assembly, _ = DefCases()
    Presentation = CastValue(dict[str, object], PartCase["presentation"])
    EmptyPreferences: dict[str, object] = {}
    Cases.extend(
        (
            PartCase | {"density_kg_m3": False},
            PartCase | {"density_kg_m3": 0.0},
            PartCase | {"presentation": Presentation | {"detail_flags": [64]}},
            PartCase | {"presentation": Presentation | {"journal_name": ""}},
            PartCase
            | {"presentation": Presentation | {"journal_name": "part\x00name"}},
            Assembly | {"save_as_part_preferences": EmptyPreferences},
        )
    )
    Reports = RunDefProcess(Cases)
    assert len(Reports) == 10
    assert all(
        Value["passed"] is False and Value["runtime_input_reads"] == 0
        for Value in Reports
    )
