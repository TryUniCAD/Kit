from tests.CliResearch.Reports.ReplayEvidence import VerifyReplay
from tests.CliResearch.Reports.HoldoutEvidence import VerifyHoldout
from hashlib import sha256 as ShaDigest
from json import loads as LoadJson
from os import environ as ProcessEnvironment, pathsep as PathSeparator
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonPath

from tests.CliResearch.ResearchRoot import ResearchRoot
from tests.Research.Inference.AdviceProvider import SetProviderMut


# a separately supplied holdout remains outside training in a sparse checkout
def CheckHoldout(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    Checkout = TmpPath / "checkout"
    RunProcess(
        ["git", "clone", "--shared", "--no-checkout", str(RootPath), str(Checkout)],
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
            "!/re/solidworks/examples/**/CUBIERTA.SLDPRT",
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
    Source = next(
        (Checkout / "re/solidworks/examples").glob("*/RUEDA DE TURBINA.SLDPRT")
    )
    Control = next((RootPath / "re/solidworks/examples").glob("*/CUBIERTA.SLDPRT"))
    Output = TmpPath / "run"
    Environment = {
        **ProcessEnvironment,
        "PYTHONPATH": str(Checkout / "src") + PathSeparator + str(Checkout / "Cli"),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    SetProviderMut(Environment, TmpPath)
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
            "--control",
            str(Control),
            "--directory",
            str(Output),
            "--advisor",
            "codex",
            "--advice-calls",
            "1",
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
    assert not (Checkout / Control.relative_to(RootPath)).exists()
    ControlPin = ShaDigest(Control.read_bytes()).hexdigest()
    assert LoadJson((Output / "FileScope.json").read_bytes())[
        "supplied_control_sha256"
    ] == [ControlPin]
    Evidence = LoadJson((Output / "Input-dimension-evidence.json").read_bytes())
    assert Evidence["supplied_controls"] == [
        {"sha256": ControlPin, "eligible_for_discovery": False}
    ]
    assert Evidence["discovered_feature_fields"]["predictions"] == []
    Passes = LoadJson((Output / "Input-reader-passes.json").read_bytes())
    assert Passes["stop"] == "no_verified_patch"
    assert Passes["passes"] == []
    assert not (Output / "Reader.patch").exists()
    VerifyHoldout(Output, TmpPath, Source, Evidence)


# a supplied candidate exercises reader promotion independently of corpus discovery eligibility
def CheckReplay(TmpPath: FilePath, MonkeyPatch) -> None:
    from shutil import copytree as CopyTree
    from struct import unpack_from as UnpackFrom

    from convert.adapters.solidworks.Container.Container import SldprtArchive

    RootPath = ResearchRoot()
    MonkeyPatch.syspath_prepend(str(RootPath / "re/automation"))
    from InferenceGrid.ReaderPass import reader_passes

    Source = next(
        (RootPath / "re/solidworks/examples").glob("*/RUEDA DE TURBINA.SLDPRT")
    )
    Stream = "Contents/Config-0-ResolvedFeatures"
    Payload = SldprtArchive.FromBytes(Source.read_bytes()).Streams[Stream]
    Offset = 40475
    Native = UnpackFrom("<d", Payload, Offset)[0]
    assert Native == UnpackFrom("<d", Payload, Offset + 537)[0]
    Before = TmpPath / "before.json"
    Command = [
        PythonPath,
        "-m",
        "KitCli",
        "decode",
        str(Source),
        "--from",
        "solidworks.sldprt",
        "-o",
    ]
    RunProcess([*Command, str(Before)], cwd=RootPath, check=True, timeout=180)
    Document = LoadJson(Before.read_bytes())["document"]
    Field = ["CirPattern", "D2", "angle"]
    Reports = reader_passes(
        RootPath,
        Source,
        TmpPath,
        dict(ProcessEnvironment),
        Document,
        {
            "discovered_feature_fields": {
                "input_sha256": ShaDigest(Source.read_bytes()).hexdigest(),
                "rules": [{"key": Field, "copies": [[537, 1]]}],
                "predictions": [
                    {
                        "key": Field,
                        "feature_id": 65,
                        "stream": Stream,
                        "scalar_offset": Offset,
                        "native_value": Native,
                        "keyword_matches": True,
                    }
                ],
            }
        },
    )
    Target = "sldprt:parameter:65:D2"
    assert Reports["reader-passes"]["passes"][0]["changed_parameters"] == [Target]
    assert Reports["reader-passes"]["stop"] == "no_verified_patch"
    assert (TmpPath / "reader-pass-1/evidence.json").is_file()
    Checkout = TmpPath / "replay"
    CopyTree(RootPath / "src", Checkout / "src")
    RunProcess(
        ["git", "apply", "--no-index", "-"],
        cwd=Checkout,
        input=Reports["reader-patch"]["patch"],
        text=True,
        check=True,
    )
    VerifyReplay(TmpPath, Command, Checkout, RootPath, Target, Native, Stream, Offset)
