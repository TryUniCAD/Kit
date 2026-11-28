from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Composition.SavePartFile import SavePartFile
from tests.Convert.Solidworks.Research.FreshPartInput import MakePartInput
from tests.Convert.Solidworks.Research.FreshPartRunner import RunFreshPart
from tests.Convert.Solidworks.Research.FreshPartTests import AssertPart


# a referenced generated child needs its own identity in both persisted header archives
def TestPartFile() -> None:
    ModelName, FileName = "GeneratedChildModel", "GeneratedChildFile"
    PathValue = "C:\\Users\\Public\\Documents\\KitOracle\\" + FileName + ".SLDPRT"
    Vertices = [[0.0, 0.0], [0.02, 0.0], [0.02, 0.01], [0.0, 0.01]]
    Depth = 0.007
    Request = MakePartInput(Vertices, Depth, ModelName)
    Provenance = CastValue(dict[str, object], Request["provenance"])
    Document = CastValue(dict[str, object], Request["document"])
    SavedAt = CastValue(int, Provenance["modified_at"]) + 51
    Request["output"] = {"path_name": PathValue, "saved_at": SavedAt}
    Report = RunFreshPart(Request)
    AssertPart(Report, 4, Depth, StreamCount=9)
    assert Report["self_reference"] == {
        "class": "moExtObject_c",
        "path": PathValue,
        "name": ModelName,
        "creation_time": Provenance["created_at"],
        "document_kind": 2,
        "configuration": {"f08": Document["configuration_name"], "f10": 0},
        "record": {
            "f48": 1,
            "f4c": 0,
            "f50": 0,
            "f54": 0,
            "f58": 0,
            "f60": SavedAt,
            "f70": 0,
            "f78": -1,
        },
    }
    assert Report["self_reference_headers_agree"] is True
    assert Report["self_reference_direct_slots"] == [3]
    assert Report["configuration_manager_header"] == {
        "class": "dmConfigMgrHeader_c",
        "saved_at": SavedAt,
        "active_configurations": [
            {
                "class": "dmConfigHeader_c",
                "name": Document["configuration_name"],
                "id": 0,
            }
        ],
        "update_stamps_agree": True,
        "sort_order_agrees": True,
    }
    SavePartFile(FileName, Request, Report)
