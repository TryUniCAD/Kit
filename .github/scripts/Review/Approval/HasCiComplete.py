from typing import cast

from ApiCall import ApiCall
from ObjectMap import ObjectMap


# native actions outside the phase aggregate must also finish before approval can be published
def HasCiComplete(RepoName: str, HeadSha: str) -> bool:
    for PageNum in range(1, 32):
        PageData = ObjectMap(
            ApiCall(
                f"repos/{RepoName}/commits/{HeadSha}/check-runs?app_id=15368&filter=latest&per_page=100&page={PageNum}"
            )
        )
        Entries = cast(list[object], PageData["check_runs"])
        for Entry in Entries:
            CheckData = ObjectMap(Entry)
            if CheckData["status"] != "completed" or CheckData["conclusion"] not in (
                "success",
                "skipped",
            ):
                return False
        if len(Entries) < 100:
            return True
    return False
