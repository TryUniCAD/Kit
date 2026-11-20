from hashlib import sha256 as Sha256
from json import loads as LoadJson
from os import environ as ProcessEnvironment, pathsep as PathSeparator
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonPath

from tests.CliResearch.ResearchRoot import ResearchRoot
from tests.Research.Inference.AdviceProvider import SetProviderMut


# a separately supplied holdout remains outside training in a sparse checkout
def CheckReservedControlReplay(TmpPath: FilePath) -> None:
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
    Control = next((Root / "re/solidworks/examples").glob("*/CUBIERTA.SLDPRT"))
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
    assert not (Checkout / Control.relative_to(Root)).exists()
    ControlPin = Sha256(Control.read_bytes()).hexdigest()
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
    Stall = LoadJson((Output / "FileStall.json").read_bytes())
    assert Stall["source_sha256"] == Evidence["input_sha256"]
    assert Stall["focus"] == "ambiguous_dimension"
    assert Stall["signed_extrusion_layout_refuted_on_searched_fields"]
    Request = LoadJson((Output / "FileAdvice/Request.json").read_bytes())
    assert "no match" in Request["packet"]["discovery_summary"]
    assert Source.name not in str(Request["packet"])
    assert Evidence["input_sha256"] not in str(Request["packet"])
    Answer = LoadJson((Output / "FileAdvice/Advice.json").read_bytes())
    assert Answer["status"] == "proposal" and Answer["verified_rule"] is False
    assert (TmpPath / "Calls").read_text().splitlines() == ["called"]
    Experiments = LoadJson((Output / "FileExperiments.json").read_bytes())
    assert Experiments["advisor_selection"] == "vary blind cut depth"
    Cut, Boss = Experiments["results"]
    assert Cut["controlled_change"] == Experiments["advisor_selection"]
    assert Cut["status"] == Boss["status"] == "no_target_match"
    assert (
        Cut["comparisons"][0]["input_value"],
        Cut["comparisons"][0]["control_value"],
    ) == (0.004, 0.005)
    assert (
        Boss["comparisons"][0]["input_value"],
        Boss["comparisons"][0]["control_value"],
    ) == (0.01, 0.012)


# a supplied candidate exercises reader promotion independently of corpus discovery eligibility
def CheckPatchReplay(TmpPath: FilePath, monkeypatch) -> None:
    from math import degrees as Degrees
    from shutil import copytree as CopyTree
    from struct import unpack_from as UnpackFrom

    from convert.adapters.solidworks.Container.Container import SldprtArchive

    Root = ResearchRoot()
    monkeypatch.syspath_prepend(str(Root / "re/automation"))
    from InferenceGrid.ReaderPass import reader_passes

    Source = next((Root / "re/solidworks/examples").glob("*/RUEDA DE TURBINA.SLDPRT"))
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
    RunProcess([*Command, str(Before)], cwd=Root, check=True, timeout=180)
    Document = LoadJson(Before.read_bytes())["document"]
    Field = ["CirPattern", "D2", "angle"]
    Reports = reader_passes(
        Root,
        Source,
        TmpPath,
        dict(ProcessEnvironment),
        Document,
        {
            "discovered_feature_fields": {
                "input_sha256": Sha256(Source.read_bytes()).hexdigest(),
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
    CopyTree(Root / "src", Checkout / "src")
    RunProcess(
        ["git", "apply", "--no-index", "-"],
        cwd=Checkout,
        input=Reports["reader-patch"]["patch"],
        text=True,
        check=True,
    )
    After = TmpPath / "after.json"
    RunProcess(
        [*Command, str(After)],
        cwd=Checkout,
        check=True,
        timeout=180,
        env={
            **ProcessEnvironment,
            "PYTHONPATH": PathSeparator.join(
                map(str, (Checkout / "src", Root / "Cli"))
            ),
        },
    )
    (Parameter,) = [
        entry
        for entry in LoadJson(After.read_bytes())["document"]["parameters"]["$tuple"]
        if entry["id"] == Target
    ]
    assert Parameter["value"]["value"] == Degrees(Native)
    assert Parameter["attributes"]["native_value"] == Native
    (Span,) = Parameter["provenance"]["spans"]["$tuple"]
    assert (Span["stream"], Span["offset"], Span["length"], Span["record_kind"]) == (
        Stream,
        Offset,
        8,
        "dimension-scalar",
    )
