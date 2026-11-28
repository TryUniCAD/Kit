from urllib.parse import quote

from ApiCall import ApiCall
from ObjectMap import ObjectMap


# review admission must bind trusted authors and live revisions without depending on approval readiness
def CheckPull(RepoName: str, Evidence: dict[str, object]) -> dict[str, object]:
    PullNumber = Evidence["pull_number"]
    if type(PullNumber) is not int or PullNumber < 1:
        raise ValueError("Invalid PR number")
    PullData = ObjectMap(ApiCall(f"repos/{RepoName}/pulls/{PullNumber}"))
    HeadData = ObjectMap(PullData["head"])
    BaseData = ObjectMap(PullData["base"])
    LiveBase = ObjectMap(
        ApiCall(
            f"repos/{RepoName}/git/ref/heads/{quote(str(BaseData['ref']), safe='/')}"
        )
    )
    if (
        PullData["state"] != "open"
        or ObjectMap(HeadData["repo"])["full_name"] != RepoName
        or ObjectMap(BaseData["repo"])["full_name"] != RepoName
        or HeadData["sha"] != Evidence["head_sha"]
        or ObjectMap(LiveBase["object"])["sha"] != Evidence["base_sha"]
        or ObjectMap(BaseData["repo"])["id"] != Evidence["repository_id"]
        or (
            "title" in Evidence
            and (PullData["title"], PullData["body"])
            != (Evidence["title"], Evidence["body"])
        )
    ):
        raise ValueError(
            "PR is untrusted or its head or live base changed since selection"
        )
    if Evidence.get("authorized_request") is not True:
        AuthorName = str(ObjectMap(PullData["user"])["login"])
        Permission = ObjectMap(
            ApiCall(f"repos/{RepoName}/collaborators/{AuthorName}/permission")
        )
        if Permission["permission"] not in ("write", "admin", "maintain"):
            raise ValueError("PR needs an authorized collaborator review request")
    return PullData
