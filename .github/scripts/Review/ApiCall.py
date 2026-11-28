import json as JsonTools
import os as OsTools
import re as RegexTools
import subprocess as ProcessTools
from typing import cast


# callers need bounded authenticated requests without placing tokens in command arguments
def ApiCall(
    Route: str,
    Payload: dict[str, object] | None = None,
    MethodName: str | None = None,
) -> object:
    CheckedRoute = RegexTools.sub(
        r"/compare/[0-9a-f]{40}\.\.\.[0-9a-f]{40}(?=\?|$)", "/compare/revisions", Route
    )
    if (
        not Route.startswith(("repos/", "orgs/", "apps/", "users/"))
        or ".." in CheckedRoute
    ):
        raise ValueError("Unexpected API route")
    Arguments = ["gh", "api", Route, "--hostname", "github.com"]
    if MethodName is not None:
        if MethodName not in ("GET", "POST", "DELETE"):
            raise ValueError("Unexpected API method")
        Arguments.extend(["--method", MethodName])
    if Payload is not None:
        if MethodName is None:
            Arguments.extend(["--method", "POST"])
        Arguments.extend(["--input", "-"])
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
    return (
        cast(object, JsonTools.loads(Result.stdout)) if Result.stdout.strip() else None
    )
