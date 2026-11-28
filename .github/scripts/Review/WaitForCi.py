from ApiCall import ApiCall
from ObjectMap import ObjectMap


# requests without eligible ci need an acknowledgement that cannot be mistaken for approval
def WaitForCi(
    RepoName: str,
    EventData: dict[str, object],
    Settings: dict[str, object],
    RequestId: int,
) -> None:
    PullNumber = int(str(ObjectMap(EventData["issue"])["number"]))
    PullInfo = ObjectMap(ApiCall(f"repos/{RepoName}/pulls/{PullNumber}"))
    ApiCall(
        f"repos/{RepoName}/check-runs",
        {
            "name": Settings["CheckName"],
            "head_sha": ObjectMap(PullInfo["head"])["sha"],
            "status": "completed",
            "conclusion": "neutral",
            "output": {
                "title": "Mention requires current successful CI",
                "summary": f"No eligible successful CI evidence was found for this PR.\n\nMention comment: {RequestId}\n\nCI run: unavailable",
            },
        },
    )
