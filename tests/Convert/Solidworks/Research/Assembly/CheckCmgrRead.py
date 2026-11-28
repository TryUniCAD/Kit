from base64 import b64decode as DecodeBytes
from pathlib import Path as FilePath
from typing import cast as CastValue

from convert import open_document as OpenDocument
from tests.Convert.Solidworks.Research.Assembly.RootRequest import RootRequest
from tests.Convert.Solidworks.Research.Assembly.RunRootProcess import RunRootProcess


# normal assembly metadata must use typed manager ownership without requiring unadmitted mate projection
def CheckCmgrRead(OutputDir: FilePath, ConfigName: str) -> FilePath:
    Request = RootRequest("TypedManagerRead", 0.25)
    Request["configuration_name"] = ConfigName
    Provenance = CastValue(dict[str, int], Request["provenance"])
    Request["output"] = {
        "path_name": "C:\\generated\\TypedManagerRead.SLDASM",
        "saved_at": Provenance["modified_at"] + 75,
    }
    Report = RunRootProcess({**Request, "include_xml_metadata": True})
    assert Report["denied_reads"] == [] and Report["manager_bytes_identical"] is True
    ParentPath = OutputDir / "TypedManagerRead.SLDASM"
    with ParentPath.open("xb") as Output:
        _ = Output.write(DecodeBytes(CastValue(str, Report["blob"]), validate=True))
    Document = OpenDocument(ParentPath, include_brep=False, include_tessellation=False)
    InfoValue = CastValue(
        dict[str, object], Document.metadata["solidworks.typed_configuration_manager"]
    )
    assert InfoValue["status"] == "complete" and InfoValue["full_linked_graph"] is False
    (ConfigRow,) = CastValue(tuple[dict[str, object], ...], InfoValue["configurations"])
    assert ConfigRow["name"] == ConfigName
    assert ConfigRow["native_class"] == "moConfiguration_c"
    assert ConfigRow["selected_by_f360"] is ConfigRow["selected_by_f368"] is True
    return ParentPath
