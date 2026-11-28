import hashlib as HashTools
import json as JsonTools
from urllib.parse import quote

from ApiCall import ApiCall
from CheckPull import CheckPull
from ObjectMap import ObjectMap


# reviews need immutable live source identities even before ci or mergeability becomes available
def ReadSnapshot(
    RepoName: str, PullNumber: int, Settings: dict[str, object]
) -> dict[str, object]:
    PullData = ObjectMap(ApiCall(f"repos/{RepoName}/pulls/{PullNumber}"))
    HeadData = ObjectMap(PullData["head"])
    BaseData = ObjectMap(PullData["base"])
    BaseRef = str(BaseData["ref"])
    LiveBase = ObjectMap(
        ApiCall(f"repos/{RepoName}/git/ref/heads/{quote(BaseRef, safe='/')}")
    )
    BaseSha = ObjectMap(LiveBase["object"])["sha"]
    Evidence = {
        "format": "review-snapshot-v2",
        "repository_id": ObjectMap(BaseData["repo"])["id"],
        "head_repository_id": ObjectMap(HeadData["repo"])["id"],
        "pull_number": PullNumber,
        "head_sha": HeadData["sha"],
        "base_sha": BaseSha,
        "base_ref": BaseRef,
        "title": PullData["title"],
        "body": PullData["body"],
        "policy_sha": Settings["PolicyRevision"],
        "model": Settings["Model"],
        "reasoning_effort": Settings["ReasoningEffort"],
    }
    Evidence["review_id"] = (
        "review:"
        + HashTools.sha256(
            JsonTools.dumps(Evidence, sort_keys=True).encode()
        ).hexdigest()
    )
    Evidence["authorized_request"] = Settings.get("TrustedRequest") is True
    CheckPull(RepoName, Evidence)
    return Evidence
