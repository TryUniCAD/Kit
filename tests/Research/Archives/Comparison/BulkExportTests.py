from hashlib import sha256 as DigestBytes
from json import dumps as EncodeJson, loads as ParseJson
from pathlib import Path as FilePath

from tests.Research.Archives.Comparison.BulkExportInput import WriteExportMut
from tests.Research.Archives.Comparison.BulkProcess import RunBulk


# historical decoder exports need process evidence without promoting retained source data into qualified semantics
def CheckExports(TmpPath: FilePath) -> None:
    OriginalPins: dict[FilePath, str] = {}
    InputProof: dict[str, dict[str, str]] = {}
    for FileName, CaseName, FormatName in (
        ("Fusion.json", "fusion-000", "fusion.f3d"),
        ("Solidworks.json", "solidworks-058", "solidworks.sldprt"),
    ):
        InputProof[FileName] = WriteExportMut(
            TmpPath / FileName, CaseName, FormatName, OriginalPins
        )
    Manifest = TmpPath / "Pairs.json"
    _ = Manifest.write_text(
        EncodeJson(
            {
                "version": 1,
                "pairs": [
                    {
                        "id": "cross-format",
                        "left": "Fusion.json",
                        "right": "Solidworks.json",
                    },
                    {
                        "id": "fusion-self",
                        "left": "Fusion.json",
                        "right": "Fusion.json",
                    },
                    {
                        "id": "solidworks-self",
                        "left": "Solidworks.json",
                        "right": "Solidworks.json",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    OriginalPins[Manifest] = DigestBytes(Manifest.read_bytes()).hexdigest()
    Output = TmpPath / "Output"
    Result = RunBulk(
        [
            "--manifest",
            str(Manifest),
            "--left-unit",
            "mm",
            "--right-unit",
            "mm",
            "--output",
            str(Output),
        ],
        UseUnits=False,
    )
    assert Result.returncode == 3, Result.stderr + Result.stdout
    Summary = ParseJson((Output / "summary.json").read_text(encoding="utf-8"))
    assert (
        Summary["pair_count"],
        Summary["manifest_sha256"],
        Summary["geometry_units"],
        Summary["exit_code"],
        Summary["native_acceptance"],
        Summary["semantic_qualification"],
    ) == (
        3,
        OriginalPins[Manifest],
        {"left": "mm", "right": "mm"},
        3,
        "not_established",
        "unverified",
    )
    assert {PairRow["id"] for PairRow in Summary["pairs"]} == {
        "cross-format",
        "fusion-self",
        "solidworks-self",
    }
    for PairRow in Summary["pairs"]:
        assert (
            PairRow["status"] in {"different", "unresolved", "ambiguous"}
            and PairRow["counts"]["matched_features"] > 0
            and PairRow["counts"]["source_issues"] > 0
        )
        ReportBytes = (Output / PairRow["report"]["path"]).read_bytes()
        assert (len(ReportBytes), DigestBytes(ReportBytes).hexdigest()) == (
            PairRow["report"]["size_bytes"],
            PairRow["report"]["sha256"],
        )
        Detail = ParseJson(ReportBytes)
        assert (
            Detail["pair_id"],
            Detail["status"],
            Detail["input_sha256"],
            Detail["native_acceptance"],
            Detail["semantic_qualification"],
            Detail["independent_source_inventory"],
        ) == (
            PairRow["id"],
            PairRow["status"],
            PairRow["input_sha256"],
            "not_established",
            "unverified",
            "not_supplied",
        )
        for SideName in ("left", "right"):
            FileName = FilePath(PairRow["inputs"][SideName]).name
            assert {
                "input_sha256": Detail["input_sha256"][SideName],
                "source_sha256": Detail["sources"][SideName]["source_sha256"],
                "source_identity_sha256": Detail["sources"][SideName][
                    "source_identity_sha256"
                ],
            } == InputProof[FileName]
            assert Detail["sources"][SideName][
                "declared_geometry_unit"
            ] == "mm" and any(
                Issue["path"] == "/metadata"
                and Issue["reason"] == "domain_requires_independent_comparison"
                for Issue in Detail["sources"][SideName]["unresolved"]
            )
        if PairRow["id"] == "cross-format":
            assert (
                Detail["sources"]["left"]["format"],
                Detail["sources"]["right"]["format"],
            ) == (
                "fusion.f3d",
                "solidworks.sldprt",
            )
    assert {
        SourcePath: DigestBytes(SourcePath.read_bytes()).hexdigest()
        for SourcePath in OriginalPins
    } == OriginalPins
