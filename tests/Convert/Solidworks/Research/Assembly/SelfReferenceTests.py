from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Assembly.EmptyAssemblyArtifacts import (
    SaveCandidate,
)
from tests.Convert.Solidworks.Research.Assembly.RootRequest import RootRequest
from tests.Convert.Solidworks.Research.Assembly.RunRootProcess import RunRootProcess


# generated directory identity must survive independent header and configuration loads
def TestSelfReference() -> None:
    NameValue, FileName = "SelfReferenceModel", "SelfReferenceFile"
    PathValue = "C:\\Users\\Public\\Documents\\KitOracle\\" + FileName + ".SLDASM"
    Request = RootRequest(NameValue, 0.25)
    Provenance = CastValue(dict[str, object], Request["provenance"])
    SavedAt = CastValue(int, Provenance["modified_at"]) + 37
    Request["output"] = {"path_name": PathValue, "saved_at": SavedAt}
    Report = RunRootProcess(Request)
    assert Report["self_reference"] == {
        "class": "moExtObject_c",
        "path": PathValue,
        "name": NameValue,
        "creation_time": Provenance["created_at"],
        "document_kind": 3,
        "configuration": {"f08": Request["configuration_name"], "f10": 0},
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
    assert all(CastValue(dict[str, bool], Report["metadata_roundtrips"]).values())
    assert Report["reconstructed_bytes_identical"] is Report["maps_consistent"] is True
    assert Report["resolved_bytes_identical"] is Report["empty_mates_linked"] is True
    assert Report["denied_reads"] == []
    SaveCandidate(FileName, Request, Report)
