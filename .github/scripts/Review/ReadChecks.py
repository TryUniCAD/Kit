from typing import cast
from urllib.parse import urlencode

from ApiCall import ApiCall
from ObjectMap import ObjectMap


# every app receipt must remain discoverable when repeated reviews share a check name
def ReadChecks(
    RepoName: str, HeadSha: str, Settings: dict[str, object]
) -> list[dict[str, object]]:
    Records: list[dict[str, object]] = []
    for PageNum in range(1, 32):
        QueryText = urlencode(
            {
                "app_id": str(Settings["AppId"]),
                "check_name": str(Settings["CheckName"]),
                "filter": "all",
                "per_page": 100,
                "page": PageNum,
            }
        )
        CheckData = ObjectMap(
            ApiCall(f"repos/{RepoName}/commits/{HeadSha}/check-runs?{QueryText}")
        )
        Entries = cast(list[object], CheckData["check_runs"])
        Records.extend(ObjectMap(Entry) for Entry in Entries)
        if len(Entries) < 100:
            return Records
    raise ValueError("App receipt inventory exceeded review limit")
