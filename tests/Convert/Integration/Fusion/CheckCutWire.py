import json as JsonLib
from pathlib import Path as FilePath
from tests.Convert.Integration.Fusion.CutCliCase import CutCliCase


# editable cut intent requires live owned controls and the original target body after serialization
def CheckCutWire(Output: FilePath, Sample: CutCliCase) -> None:
    Document = JsonLib.loads(Output.read_text())["document"]
    Features = Document["feature_timeline"]["$tuple"]
    assert (
        len(Features) == 4
        and tuple(Value["name"] for Value in Features) == Sample.StepNames
    )
    Stock, ToolCut = Features[1], Features[3]
    Definition = ToolCut["definition"]
    assert (
        Stock["definition"]["$type"] == "DistanceExtrude"
        and Definition["$type"] == "DistanceCut"
    )
    assert ToolCut["operation"]["value"] == "cut"
    Bodies = Document["bodies"]["$tuple"]
    assert Definition["target_body_ids"]["$tuple"] == [Bodies[0]["id"]]
    assert Bodies[0]["final_feature_id"] == ToolCut["id"]
    assert (
        Stock["output_body_ids"]["$tuple"]
        == ToolCut["output_body_ids"]["$tuple"]
        == [Bodies[0]["id"]]
    )
    assert ToolCut["input_feature_ids"]["$tuple"] == [Stock["id"], Features[2]["id"]]
    Parameters = {Value["id"]: Value for Value in Document["parameters"]["$tuple"]}
    for Feature, Extent, ParamName in (
        (Stock, Stock["definition"], Sample.StockParam),
        (ToolCut, Definition["extrusion"], Sample.CutParam),
    ):
        Along, Taper = (
            Parameters[Extent["along_parameter_id"]],
            Parameters[Extent["taper_parameter_id"]],
        )
        assert (
            Along["name"] == ParamName
            and Along["attributes"]["native_name"] == "AlongDistance"
        )
        assert Taper["attributes"]["native_name"] == "TaperAngle"
        assert Along["owner_id"] == Taper["owner_id"] == Feature["id"]
        assert Feature["parameter_ids"]["$tuple"] == [Along["id"], Taper["id"]]
    assert (
        len(Document["sketches"]["$tuple"]) == 2
        and Document["metadata"]["fusion.read_only"] is True
    )
