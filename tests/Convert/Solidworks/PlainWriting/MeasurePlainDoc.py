from json import loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue
from zlib import ZLIB_RUNTIME_VERSION as DeflateRuntime

from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Solidworks.PlainWriting.MakePlainDoc import MakePlainDoc

# these neutral inputs reproduce the two independently measured disclosed parts
KMeasuredCases = {
    "Skew": (
        "sdk factory skew",
        ((-14.2, -3.8), (24.9, 1.7), (4.1, 29.5)),
        12.75,
    ),
    "Step": (
        "sdk 設計 stepped",
        (
            (-13.1, -10.2),
            (28.4, -10.2),
            (28.4, 23.7),
            (6.7, 23.7),
            (6.7, 6.4),
            (-13.1, 6.4),
        ),
        18.625,
    ),
}

# the committed receipt carries only evidence while the neutral requests supply geometry
KMeasureRoot = FilePath(__file__).resolve().parents[4]


# the original disclosed writer epoch and report belong to the hosted evidence fixture
def MeasurePlainDoc(
    RoleName: str,
) -> tuple[CadDocument, dict[str, object], str]:
    NameValue, Corners, DepthValue = KMeasuredCases[RoleName]
    ReceiptName = (
        "SdkDefaultPartZlibNgNative01.json"
        if "zlib-ng" in DeflateRuntime
        else "SdkDefaultPartNative01.json"
    )
    ReceiptPath = KMeasureRoot / "re/solidworks/measurements/2026" / ReceiptName
    Receipt = CastValue(dict[str, object], LoadJson(ReceiptPath.read_bytes()))
    CaseRows = CastValue(list[dict[str, object]], Receipt["cases"])
    (CaseValue,) = (Value for Value in CaseRows if Value["role"] == RoleName)
    Digest = CastValue(str, CaseValue["generated_sha256"])
    return (
        MakePlainDoc(NameValue, Corners, DepthValue),
        {"written_at": 1794973072, "receipt": Receipt},
        Digest,
    )
