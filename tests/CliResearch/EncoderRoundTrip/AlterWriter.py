from json import dumps as EncodeJson, loads as DecodeJson

from pytest import approx as NearValue

from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
from interchange.document.Models.DocumentModel import CadDocument


# a valid alternative driving depth must reach native replay instead of failing typed document admission
def AlterWriter(Payload: bytes) -> bytes:
    WireValue = DecodeJson(Payload)
    assert WireValue["metadata"]["name"] == "edited"
    (Driver,) = WireValue["parameters"]["$tuple"]
    (Feature,) = WireValue["feature_timeline"]["$tuple"]
    assert Driver["value"]["value"] == Feature["definition"]["length"]["value"] == 12.19
    Driver["value"]["value"] = 12.21
    Feature["definition"]["length"]["value"] = 12.21
    Document = CadDocument.from_dict(WireValue)
    Document.assert_valid()
    assert Document.metadata["name"] == "edited"
    assert PlanPartWrite(Document).DepthValue == NearValue(12.21 / 1000.0)
    return (
        EncodeJson(
            Document.to_dict(),
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
