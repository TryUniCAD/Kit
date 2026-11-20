from json import loads as LoadJson
from os import environ as ProcessEnvironment, pathsep as PathSeparator
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonPath

from tests.CliResearch.ResearchRoot import ResearchRoot


# held back reader bindings exercise successive source changes through the public file command
def CheckSuccessiveReaderPasses(TmpPath: FilePath) -> None:
    Root = ResearchRoot()
    Checkout = TmpPath / "checkout"
    RunProcess(
        ["git", "clone", "--shared", "--no-checkout", str(Root), str(Checkout)],
        check=True,
    )
    RunProcess(
        [
            "git",
            "sparse-checkout",
            "set",
            "--no-cone",
            "/src/",
            "/Cli/",
            "/re/automation/",
            "/re/solidworks/examples/",
            "/re/Fusion/Study/*.py",
            "!/re/Fusion/Study/*/",
            "/pyproject.toml",
        ],
        cwd=Checkout,
        check=True,
    )
    RunProcess(
        ["git", "checkout", "--detach", ProcessEnvironment["GITHUB_SHA"]],
        cwd=Checkout,
        check=True,
    )
    Field = Checkout / "src/convert/adapters/solidworks/Core/BindMirroredField.py"
    Counts = Field.with_name("Native.py")
    Text = Field.read_text()
    Start = Text.index(" = {", Text.index("KMirroredFields:")) + 3
    Field.write_text(Text[:Start] + "{}" + Text[Text.index("\n\n", Start) :])
    Text = Counts.read_text()
    Start = Text.index(" = ", Text.index("KFeatureCountCopies:")) + 3
    Counts.write_text(Text[:Start] + "()" + Text[Text.index("\n", Start) :])
    RunProcess(
        [
            "git",
            "-c",
            "user.name=Research",
            "-c",
            "user.email=research@example.invalid",
            "commit",
            "--no-verify",
            "-am",
            "Hold back two reader rule families",
        ],
        cwd=Checkout,
        check=True,
    )
    Source = next(
        (Checkout / "re/solidworks/examples").glob("*/RUEDA DE TURBINA.SLDPRT")
    )
    Output = TmpPath / "run"
    Environment = {
        **ProcessEnvironment,
        "PYTHONPATH": str(Checkout / "src") + PathSeparator + str(Checkout / "Cli"),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    Result = RunProcess(
        [
            PythonPath,
            "-m",
            "KitCli",
            "run",
            "--root",
            str(Checkout),
            "solidworks",
            "--input",
            str(Source),
            "--directory",
            str(Output),
            "--workers",
            "1",
            "--reserved-memory-mib",
            "512",
        ],
        cwd=Checkout,
        env=Environment,
        capture_output=True,
        timeout=300,
    )
    assert Result.returncode == 2, Result.stderr
    assert (Output / "MirroredFields.patch").is_file()
    assert (Output / "SketchPatternCounts.patch").is_file()
    Passes = LoadJson((Output / "Input-reader-passes.json").read_bytes())
    assert Passes["stop"] == "no_verified_patch"
    assert [Row["generator"] for Row in Passes["passes"]] == [
        "mirrored-field-reader",
        "pattern-count-reader",
    ]
    assert [len(Row["changed_parameters"]) for Row in Passes["passes"]] == [1, 2]
    RunProcess(["git", "apply", str(Output / "Reader.patch")], cwd=Checkout, check=True)
    Strict = TmpPath / "strict.json"
    RunProcess(
        [
            PythonPath,
            "-m",
            "KitCli",
            "decode",
            str(Source),
            "--from",
            "solidworks.sldprt",
            "-o",
            str(Strict),
        ],
        env=Environment,
        cwd=Checkout,
        check=True,
        timeout=180,
    )
    Document = LoadJson(Strict.read_bytes())["document"]
    assert Document["source"]["sha256"] == Passes["input_sha256"]
    Values = {Row["id"]: Row["value"] for Row in Document["parameters"]["$tuple"]}
    assert abs(Values["sldprt:parameter:65:D2"]["value"] - 32.72727273) < 1e-9
    for Id in ("sldprt:parameter:65:D1", "sldprt:parameter:257:D1"):
        assert Values[Id]["kind"]["value"] == "integer"
        assert Values[Id]["value"] == 11
