import json as JsonLib
from pathlib import Path as FilePath
from subprocess import run as RunProcess

import pytest as Pytest


# cleanup must preserve current acceptance while releasing abandoned runners through the complete workflow entry point
@Pytest.mark.parametrize(
    "CaseName",
    (
        "abandoned",
        "queued",
        "waiting",
        "pending",
        "requested",
        "completed",
        "manual",
        "pull",
        "workflow",
        "fork",
        "repository",
        "branch",
        "ordinary",
        "sha",
        "queue-active",
        "queue-page",
        "queue-error",
        "queue-null",
        "queue-missing",
        "ref-active",
        "ref-error",
    ),
)
def CheckCleanup(CaseName: str) -> None:
    RootPath = FilePath(__file__).resolve().parents[3]
    Outcome = RunProcess(
        ["node", str(RootPath / "tests/Policy/QueueCleanup/RunCleanup.cjs"), CaseName],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    Evidence = JsonLib.loads(Outcome.stdout)
    assert Outcome.returncode == int(
        CaseName in {"queue-error", "queue-null", "queue-missing", "ref-error"}
    ), Outcome.stderr
    assert Evidence["Cancelled"] == (
        [42]
        if CaseName in {"abandoned", "queued", "waiting", "pending", "requested"}
        else []
    )
    if Evidence["Cancelled"]:
        assert Evidence["Calls"] == ["queue", "ref", "cancel"]
    if CaseName == "queue-page":
        assert Evidence["Calls"] == ["queue", "queue"]
