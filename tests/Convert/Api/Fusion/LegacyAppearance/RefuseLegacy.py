from pathlib import Path as FilePath

from tests.Convert.Api.Fusion.LegacyAppearance.RunLegacy import RunLegacy


# malformed persisted requests must fail without yielding either logical group
def RefuseLegacy(Request: FilePath, Output: FilePath, Reason: str) -> None:
    Original = Request.read_bytes()
    Result = RunLegacy(Request, Output)
    assert Result.returncode == 1
    assert Result.stderr.strip() == Reason
    assert not Result.stdout.strip() and not tuple(Output.iterdir())
    assert Request.read_bytes() == Original
