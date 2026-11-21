from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue


# saved view inspection must preserve both owner roles and exact native coordinates
def TestSavedView() -> None:
    ProofPath = (
        FilePath(__file__).resolve().parents[4]
        / "re/tooling/sw2026/CheckSavedPartView.py"
    )
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(ProofPath), "measure"),
        capture_output=True,
        timeout=90,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stderr.decode()
    Evidence = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert (
        Evidence["guarded_processes"] == 5
        and Evidence["runtime_external_accesses"] == 0
    )
    Sources = CastValue(dict[str, dict[str, object]], Evidence["sources"])
    Ladder, Light, Local = (
        Sources[NameValue] for NameValue in ("ladder", "one_light", "local")
    )
    assert (
        Ladder["matrix_present"],
        Light["matrix_present"],
        Local["matrix_present"],
    ) == (1, 0, 0)
    assert (
        Ladder["user_environments"],
        Light["user_environments"],
        Local["user_environments"],
    ) == (1, 1, 0)
    assert (
        Ladder["pose_sha256"]
        == "1feef72863afe5a345809cd63f551528a852ff99210db26e3410f16155c3f4f7"
    )
    assert (
        Light["pose_sha256"]
        == "13aa4cce3f6ef126f73c6b7cf3f4d0f6200ae8f024d1ead28184df8794fe34f3"
    )
    Analytic = CastValue(dict[str, object], Evidence["analytic"])
    assert (
        Analytic["pose_sha256"]
        == "738d95b1f47791cf8570a6454130420c21550ff69e9cfdf822fb872af814ee32"
    )
    Refusals = CastValue(dict[str, str], Evidence["refusals"])
    assert len(Refusals) == 13
    assert (
        Refusals["model_negative_zero"]
        == "source camera contains unrepresented affine state"
    )
    assert all(
        Refusals[NameValue] == "view coordinate or scale must be finite"
        for NameValue in ("nan_pan", "infinite_zoom", "infinite_matrix")
    )
