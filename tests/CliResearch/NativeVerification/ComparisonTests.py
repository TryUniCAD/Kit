from json import loads as DecodeJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.CliResearch.NativeVerification.DecodeControl import DecodeControl
from tests.CliResearch.NativeVerification.RunComparison import RunComparison


# equal measurements need complete semantic coverage without pretending that offline evidence is native acceptance
@TestMark.parametrize("VariantName", ("original", "reordered", "near_boundary"))
def CheckFullCompare(TmpPath: FilePath, VariantName: str) -> None:
    DocumentPath = DecodeControl(TmpPath)
    Evidence = DecodeJson(
        FilePath(__file__).with_name("FusionRectangle.json").read_bytes()
    )
    if VariantName == "reordered":
        for FieldName in ("vertices_mm", "edges", "faces"):
            Evidence["bodies"][0]["geometry"][FieldName].reverse()
        for FaceValue in Evidence["bodies"][0]["geometry"]["faces"]:
            for Boundary in FaceValue["loops"]:
                Boundary.reverse()
        for FieldName in ("entities", "constraints"):
            Evidence["semantics"]["sketches"][0][FieldName].reverse()
    if VariantName == "near_boundary":
        Evidence["bodies"][0]["geometry"]["vertices_mm"][0][0] = -1e-8
    Result = RunComparison(TmpPath, DocumentPath, Evidence)
    assert Result.returncode == 0, Result.stderr
    Report = DecodeJson((TmpPath / "Compared.json").read_bytes())
    assert Report["status"] == "passed" and Report["full_semantics_verified"] is True
    assert Report["semantic_gaps"] == []
    assert Report["scope"] == "offline_measurement_comparison"
    for FieldName in (
        "native_acceptance",
        "live_batch_verified",
        "portable_complete",
        "conversion_qualified",
    ):
        assert Report[FieldName] is False


# equal counts must not conceal wrong operands definitions bindings topology or missing semantic measurements
@TestMark.parametrize(
    "FieldPath, Replacement, StatusName",
    (
        (("semantics",), None, "unverified"),
        (("semantics", "gaps"), ["unsupported_feature"], "unverified"),
        (("semantics", "features", 1, "direction"), [0, 0, -1], "failed"),
        (("semantics", "features", 1, "bindings", "length"), "height_mm", "failed"),
        (
            (
                "semantics",
                "sketches",
                0,
                "constraints",
                0,
                "operands",
                0,
                "geometry",
                "start_mm",
            ),
            [1, 0, 0],
            "failed",
        ),
        (("bodies", 0, "faces"), 7, "failed"),
        (("bodies", 0, "geometry", "faces", 0, "offset_mm"), 1, "failed"),
    ),
)
def CheckBadCompare(
    TmpPath: FilePath,
    FieldPath: tuple[str | int, ...],
    Replacement: object,
    StatusName: str,
) -> None:
    DocumentPath = DecodeControl(TmpPath)
    Evidence = DecodeJson(
        FilePath(__file__).with_name("FusionRectangle.json").read_bytes()
    )
    Cursor = Evidence
    for FieldName in FieldPath[:-1]:
        Cursor = Cursor[FieldName]
    Cursor[FieldPath[-1]] = Replacement
    Result = RunComparison(TmpPath, DocumentPath, Evidence)
    assert Result.returncode == 5, Result.stderr
    Report = DecodeJson((TmpPath / "Compared.json").read_bytes())
    assert Report["status"] == StatusName
    assert Report["full_semantics_verified"] is False
    assert Report["native_acceptance"] is False
