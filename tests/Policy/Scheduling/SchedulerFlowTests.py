from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess

import pytest as Pytest


# real workflow entry processes must preserve requests and reject uncertain admission or deployment metadata
@Pytest.mark.parametrize(
    "CaseName",
    (
        "budget-new",
        "budget-audit",
        "budget-previous",
        "budget-single",
        "budget-legacy",
        "budget-uncontrolled",
        "budget-minimum",
        "budget-wait",
        "budget-rules-error",
        "budget-invalid",
        "budget-error",
        "admit-empty",
        "admit-busy",
        "admit-stale",
        "admit-timeout",
        "admit-error",
        "lanes-even",
        "lanes-odd",
        "lanes-pull",
        "lanes-missing",
        "lanes-error",
    ),
)
def CheckScheduler(CaseName: str) -> None:
    ScriptPath = FilePath(__file__).with_name("RunScheduling.cjs")
    Outcome = RunProcess(
        ["node", str(ScriptPath), CaseName],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    Failures = {
        "budget-invalid": "Unsupported shared runner budget",
        "budget-single": "Unsupported shared runner budget",
        "lanes-missing": "could not count candidate ancestors",
        "lanes-error": "Lane API unavailable",
        "budget-error": "Budget API unavailable",
        "admit-error": "Admission API unavailable",
        "admit-timeout": "Manual audit admission timed out",
    }
    assert Outcome.returncode == int(CaseName in Failures), Outcome.stderr
    if CaseName in Failures:
        assert Failures[CaseName] in Outcome.stderr
        return
    Evidence = LoadJson(Outcome.stdout)
    if CaseName.startswith("lanes-"):
        assert Evidence["Outputs"] == {"prefix": "B-" if CaseName == "lanes-odd" else ""}
        assert Evidence["Requests"] == int(CaseName != "lanes-pull")
        return
    if CaseName.startswith("budget-"):
        Shards = LoadJson(Evidence["Outputs"]["native"])
        assert len(Shards) == (5 if CaseName in {"budget-new", "budget-previous"} else 4)
        assert [Shard["index"] for Shard in Shards] == list(range(len(Shards)))
        assert Evidence["Outputs"]["runtime-target"] == (
            "0"
            if CaseName
            in {
                "budget-legacy",
                "budget-uncontrolled",
                "budget-minimum",
                "budget-wait",
                "budget-rules-error",
            }
            else "1200"
        )
        assert Evidence["Outputs"]["max-tests"] == (
            "1200"
            if CaseName
            in {
                "budget-legacy",
                "budget-uncontrolled",
                "budget-minimum",
                "budget-wait",
                "budget-rules-error",
            }
            else "1000"
        )
        return
    assert Evidence["Pauses"] == int(CaseName in {"admit-busy", "admit-stale"})
