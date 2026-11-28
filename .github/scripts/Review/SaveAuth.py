import json as JsonTools
import os as OsTools
import subprocess as ProcessTools
from pathlib import Path

from ObjectMap import ObjectMap


# rotated session tokens must replace the stored copy before another hosted job begins
def SaveAuth() -> None:
    AuthPath = Path(OsTools.environ["RUNNER_TEMP"]) / "ReviewAuth/auth.json"
    if not AuthPath.exists():
        return
    try:
        AuthText = AuthPath.read_text()
        AuthData = ObjectMap(JsonTools.loads(AuthText))
        if AuthData.get("auth_mode") != "chatgpt" or not ObjectMap(
            AuthData["tokens"]
        ).get("refresh_token"):
            raise ValueError("Refusing to persist invalid account credentials")
        ProcessTools.run(
            [
                "gh",
                "secret",
                "set",
                "CODEX_AUTH_JSON",
                "--env",
                "AccountReview",
                "--repo",
                OsTools.environ["GITHUB_REPOSITORY"],
            ],
            input=AuthText,
            text=True,
            check=True,
            timeout=60,
            stdout=ProcessTools.DEVNULL,
            stderr=ProcessTools.DEVNULL,
        )
    finally:
        AuthPath.unlink(missing_ok=True)


if __name__ == "__main__":
    SaveAuth()
