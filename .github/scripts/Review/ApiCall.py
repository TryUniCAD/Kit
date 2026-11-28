import json as JsonTools
import os as OsTools
import subprocess as ProcessTools
from typing import cast


# callers need bounded authenticated requests without placing tokens in command arguments
def ApiCall(Route: str, Payload: dict[str, object] | None = None) -> object:
    if not Route.startswith(("repos/", "orgs/", "apps/", "users/")) or ".." in Route:
        raise ValueError("Unexpected API route")
    Arguments = ["gh", "api", Route, "--hostname", "github.com"]
    if Payload is not None:
        Arguments.extend(["--method", "POST", "--input", "-"])
    Result = ProcessTools.run(
        Arguments,
        input=None if Payload is None else JsonTools.dumps(Payload),
        text=True,
        capture_output=True,
        check=True,
        timeout=60,
        env={**OsTools.environ, "GH_HOST": "github.com"},
    )
    if len(Result.stdout) > 8_000_000:
        raise ValueError("API response exceeded review limit")
    return cast(object, JsonTools.loads(Result.stdout))
