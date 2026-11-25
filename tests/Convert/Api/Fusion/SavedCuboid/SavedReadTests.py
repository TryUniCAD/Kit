from collections import Counter
from hashlib import sha256 as HashBytes
from json import loads as ParseJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from pytest import approx as NearValue, mark as MarkTests

from convert import open_document as OpenDocument
from convert.adapters.Fusion.State.DecodeState import DecodeState
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange import CadDocument
from tests.Convert.Api.Fusion.SavedCuboid.SavedCase import SavedCase
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource


# public decoding must expose fixed corner constraints without discarding any original native state
@MarkTests.parametrize("CaseValue", KSavedCases)
def TestSavedRead(TmpPath: FilePath, CaseValue: SavedCase) -> None:
    Source = SavedSource(CaseValue)
    Payload = Source.read_bytes()
    assert HashBytes(Payload).hexdigest() == CaseValue.DigestValue
    Manifest = ParseJson((Source.parent / "Manifest.json").read_text())
    Capture = next(
        Value for Value in Manifest["fixtures"] if Value["file"] == CaseValue.FileName
    )
    ReceiptPath = Source.parent / Capture["custody_record"]
    assert ReceiptPath.resolve().is_relative_to(Source.parent.resolve())
    ReceiptBytes = ReceiptPath.read_bytes()
    assert HashBytes(ReceiptBytes).hexdigest() == Capture["custody_record_sha256"]
    Receipt = ParseJson(ReceiptBytes)
    assert Receipt["archives"][Capture["custody_archive_key"]] == CaseValue.DigestValue
    assert Capture["sha256"] == CaseValue.DigestValue
    Model = ReadDocument(Payload)
    Document = OpenDocument(Payload, source_format="f3d")
    assert not Document.diagnostics and not Document.brep_payloads
    assert len(Document.parameters) == 7
    assert len(Document.feature_timeline) == 2
    assert len(Document.bodies) == 1 and len(Document.sketches) == 1
    assert Document.bodies[0].topology.volume == NearValue(
        CaseValue.WidthMm * CaseValue.DepthMm * CaseValue.HeightMm
    )
    assert Document.metadata["fusion.read_only"] is True
    Contract = CastValue(dict[str, object], Document.metadata["fusion.native_state"])
    assert Contract["version"] == 2
    assert DecodeState(Contract["model"]) == Model
    Target = TmpPath / "Persisted.json"
    _ = Target.write_text(Document.to_json(), encoding="utf-8")
    Neutral = CadDocument.from_json(Target.read_text(encoding="utf-8"))
    assert Neutral == Document
    Persisted = CastValue(dict[str, object], Neutral.metadata["fusion.native_state"])
    assert DecodeState(Persisted["model"]) == Model
    assert len(Model.Snapshots) == 1 and Model.Graphics is not None
    assert len(Model.Previews) == 2 and len(Model.Materials) == 1
    assert Counter(Value.KindValue for Value in Model.Configurations) == {
        "rule": 1,
        "table": 1,
    }
