from dataclasses import replace as ReplaceData
from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath

from convert import open_document as OpenDocument, write_document as WriteDocument
from tests.Convert.Api.Fusion.AdapterCases import AdapterCase


# previously exported cuboid state must remain writable without the newly introduced topology tracking field
def TestLegacyPrism(TmpPath: FilePath) -> None:
    Source = TmpPath / "Source.f3d"
    _ = WriteDocument(AdapterCase("cuboid"), Source, destination_format="f3d")
    Document = OpenDocument(Source)
    Contract = DecodeJson(EncodeJson(Document.metadata["fusion.native_state"]))
    History = Contract["model"]["fields"]["Bodies"]["tuple"][0]["fields"]["History"]
    assert History["record"].endswith(".PrismHistory.PrismHistory")
    assert History["fields"]["Tracking"]["fields"]["Entries"] == {"tuple": []}
    del History["fields"]["Tracking"]
    Legacy = ReplaceData(Document, metadata={"fusion.native_state": Contract})
    Target = TmpPath / "Restored.f3d"
    _ = WriteDocument(Legacy, Target, destination_format="f3d")
    assert Target.read_bytes() == Source.read_bytes()
    assert OpenDocument(Target).feature_timeline == Document.feature_timeline
