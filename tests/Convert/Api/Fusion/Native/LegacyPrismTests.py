from dataclasses import replace as ReplaceData
from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath

from pytest import mark as MarkTests

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismIds import PrismIds
from tests.Convert.Api.Fusion.AdapterCases import AdapterCase


# public cuboid archives must preserve established bytes with either legacy or explicit empty tracking state
@MarkTests.parametrize("WithTracking", (False, True))
def TestLegacyPrism(TmpPath: FilePath, WithTracking: bool) -> None:
    Source = TmpPath / "Source.f3d"
    _ = WriteDocument(AdapterCase("cuboid"), Source, destination_format="f3d")
    Document = OpenDocument(Source)
    Contract = DecodeJson(EncodeJson(Document.metadata["fusion.native_state"]))
    History = Contract["model"]["fields"]["Bodies"]["tuple"][0]["fields"]["History"]
    assert History["record"].endswith(".PrismHistory.PrismHistory")
    assert "Tracking" not in History["fields"]
    if WithTracking:
        History["fields"]["Tracking"] = EncodeState(PrismIds())
    Legacy = ReplaceData(Document, metadata={"fusion.native_state": Contract})
    Target = TmpPath / "Restored.f3d"
    _ = WriteDocument(Legacy, Target, destination_format="f3d")
    assert Target.read_bytes() == Source.read_bytes()
    assert OpenDocument(Target).feature_timeline == Document.feature_timeline
