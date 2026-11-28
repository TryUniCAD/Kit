from urllib.parse import quote

from ApiCall import ApiCall
from ObjectMap import ObjectMap


# public triggers must never grant access to fork authors or obsolete revisions
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
        or PullData["draft"]
        or ObjectMap(HeadData["repo"])["full_name"] != RepoName
        or ObjectMap(BaseData["repo"])["full_name"] != RepoName
        or HeadData["sha"] != Evidence["head_sha"]
        or BaseData["sha"] != Evidence["base_sha"]
        or ObjectMap(LiveBase["object"])["sha"] != Evidence["base_sha"]
        or PullData.get("mergeable") is not True
        or ObjectMap(BaseData["repo"])["id"] != Evidence["repository_id"]
    ):
        raise ValueError(
            "PR is unmergeable or untrusted or its head or live base changed since CI"
        )
    AuthorName = str(ObjectMap(PullData["user"])["login"])
    Permission = ObjectMap(
        ApiCall(f"repos/{RepoName}/collaborators/{AuthorName}/permission")
    )
    if Permission["permission"] not in ("write", "admin", "maintain"):
        raise ValueError("PR author is not a trusted collaborator")
    return PullData
