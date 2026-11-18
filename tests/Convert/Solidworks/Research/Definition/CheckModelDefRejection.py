from base64 import b64decode as Decode64, b64encode as Encode64
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Definition.DefSettingsCases import (
    DefSettingsCases,
)
from tests.Convert.Solidworks.Research.Definition.RunModelDefProcess import (
    RunModelDefProcess,
)


# complete stream admission must reject unsupported revisions and malformed roots before returning a graph
def CheckModelDefRejection(BuiltValue: dict[str, object]) -> None:
    Data = Decode64(CastValue(str, BuiltValue["output"]), validate=True)
    InputValues = (Data[:-1], Data + b"\x00", Data[:20] + bytes(16) + Data[36:])
    Cases: list[dict[str, object]] = [
        {"mode": "prepare", "version": 19000, "input": Encode64(Value).decode("ascii")}
        for Value in InputValues
    ]
    Cases.append({"mode": "prepare", "version": 18000, "input": BuiltValue["output"]})
    Part, _, Assembly, _ = DefSettingsCases()
    Presentation = CastValue(dict[str, object], Part["presentation"])
    EmptyPreferences: dict[str, object] = {}
    Cases.extend(
        (
            Part | {"density_kg_m3": False},
            Part | {"density_kg_m3": 0.0},
            Part | {"presentation": Presentation | {"detail_flags": [64]}},
            Part | {"presentation": Presentation | {"journal_name": ""}},
            Part | {"presentation": Presentation | {"journal_name": "part\x00name"}},
            Assembly | {"save_as_part_preferences": EmptyPreferences},
        )
    )
    Reports = RunModelDefProcess(Cases)
    assert len(Reports) == 10
    assert all(
        Value["passed"] is False and Value["runtime_input_reads"] == 0
        for Value in Reports
    )
