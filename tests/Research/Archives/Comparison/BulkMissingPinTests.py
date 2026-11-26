from hashlib import sha256 as DigestBytes
from json import dumps as EncodeJson, loads as ParseJson
from pathlib import Path as FilePath

from pytest import mark as MarkValue

from tests.Research.Archives.Comparison.BulkProcess import RunBulk


# missing counterparts must retain every available source fingerprint without decoding incomplete pairs
@MarkValue.parametrize(
    "ModeName,PresentSide",
    (
        ("manifest", "left"),
        ("manifest", "right"),
        ("manifest", "neither"),
        ("directory", "left"),
        ("directory", "right"),
    ),
)
def CheckMissingPin(TmpPath: FilePath, ModeName: str, PresentSide: str) -> None:
    Roots = {SideName: TmpPath / SideName for SideName in ("left", "right")}
    for RootPath in Roots.values():
        RootPath.mkdir()
    Inputs = {SideName: RootPath / "Part.json" for SideName, RootPath in Roots.items()}
    if PresentSide in Inputs:
        _ = Inputs[PresentSide].write_bytes(b"fingerprinted before document decoding")
    Manifest = TmpPath / "Pairs.json"
    _ = Manifest.write_text(
        EncodeJson(
            {
                "version": 1,
                "pairs": [
                    {
                        "id": "missing",
                        **{
                            SideName: InputPath.relative_to(TmpPath).as_posix()
                            for SideName, InputPath in Inputs.items()
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    Before = {
        InputPath: InputPath.read_bytes()
        for InputPath in (*Inputs.values(), Manifest)
        if InputPath.is_file()
    }
    Output = TmpPath / "Output"
    Arguments = (
        ["--manifest", str(Manifest)]
        if ModeName == "manifest"
        else ["--left", str(Roots["left"]), "--right", str(Roots["right"])]
    )
    Result = RunBulk([*Arguments, "--output", str(Output)])
    assert Result.returncode == 1, Result.stderr + Result.stdout
    Summary = ParseJson((Output / "summary.json").read_text(encoding="utf-8"))
    assert Summary["outcomes"] == {"missing_input": 1}
    PairRow = Summary["pairs"][0]
    Report = ParseJson((Output / PairRow["report"]["path"]).read_text(encoding="utf-8"))
    Expected = {"tolerances": Summary["tolerances_sha256"]}
    if PresentSide in Inputs:
        Expected[PresentSide] = DigestBytes(Before[Inputs[PresentSide]]).hexdigest()
    assert PairRow["input_sha256"] == Report["input_sha256"] == Expected
    assert Report["missing"] == [
        SideName for SideName in Inputs if SideName != PresentSide
    ]
    assert {InputPath: InputPath.read_bytes() for InputPath in Before} == Before


# a missing counterpart must not conceal an existing path that fails plain file admission
@MarkValue.parametrize("InvalidSide", ("left", "right"))
def CheckMissingBad(TmpPath: FilePath, InvalidSide: str) -> None:
    Inputs = {
        SideName: TmpPath / (SideName + ".json") for SideName in ("left", "right")
    }
    Inputs[InvalidSide].mkdir()
    Sentinel = Inputs[InvalidSide] / "Sentinel.txt"
    _ = Sentinel.write_bytes(b"preserved input evidence")
    Manifest = TmpPath / "Pairs.json"
    _ = Manifest.write_text(
        EncodeJson(
            {
                "version": 1,
                "pairs": [
                    {
                        "id": "invalid",
                        **{
                            SideName: InputPath.name
                            for SideName, InputPath in Inputs.items()
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    Original = Manifest.read_bytes()
    Output = TmpPath / "Output"
    Result = RunBulk(["--manifest", str(Manifest), "--output", str(Output)])
    assert Result.returncode == 1, Result.stderr + Result.stdout
    Summary = ParseJson((Output / "summary.json").read_text(encoding="utf-8"))
    assert Summary["outcomes"] == {"reader_error": 1}
    PairRow = Summary["pairs"][0]
    Report = ParseJson((Output / PairRow["report"]["path"]).read_text(encoding="utf-8"))
    assert Report["error_type"] == "ValueError"
    assert Report["reason"] == "input must be a bounded plain regular file"
    assert (
        PairRow["input_sha256"]
        == Report["input_sha256"]
        == {"tolerances": Summary["tolerances_sha256"]}
    )
    assert Sentinel.read_bytes() == b"preserved input evidence"
    assert Manifest.read_bytes() == Original
