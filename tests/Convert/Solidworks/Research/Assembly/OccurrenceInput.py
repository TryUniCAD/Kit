from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Assembly.RootRequest import RootRequest
from tests.Convert.Solidworks.Research.FreshPartInput import MakePartInput


# the native batch needs authored inputs that can be regenerated from the source revision
def MakeOccInput(
    NameValue: str,
    Origin: list[float],
    AxisX: list[float],
    AxisY: list[float],
) -> dict[str, object]:
    Folder = "C:\\Users\\Public\\Documents\\KitOracle\\"
    Assembly = RootRequest(NameValue, 0.25)
    Child = MakePartInput(
        [[0.0, 0.0], [0.02, 0.0], [0.02, 0.01], [0.0, 0.01]],
        0.007,
        "GeneratedChildModel",
    )
    Provenance = CastValue(dict[str, int], Child["provenance"])
    ModifiedAt = Provenance["modified_at"]
    Assembly["output"] = {
        "path_name": Folder + NameValue + ".SLDASM",
        "saved_at": ModifiedAt + 75,
    }
    Child["output"] = {
        "path_name": Folder + "GeneratedChildFile.SLDPRT",
        "saved_at": ModifiedAt + 51,
    }
    return {
        "assembly": Assembly,
        "child": Child,
        "occurrences": [
            {
                "name": "GeneratedChildModel-1",
                "placement": {"origin": Origin, "u": AxisX, "v": AxisY},
            }
        ],
    }
