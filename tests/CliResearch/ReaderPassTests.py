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
