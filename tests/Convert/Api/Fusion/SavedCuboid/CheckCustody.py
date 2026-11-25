from hashlib import sha256 as HashBytes
from json import loads as ParseJson
from pathlib import Path as FilePath

from tests.Convert.Api.Fusion.SavedCuboid.SavedCase import SavedCase


# pinned custody evidence keeps native observations attached to the exact compatibility inputs
def CheckCustody(Source: FilePath, CaseValue: SavedCase, Payload: bytes) -> None:
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
