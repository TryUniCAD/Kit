from pathlib import Path

from ApiCall import ApiCall
from BuildContext import BuildContext
from ReadPages import ReadPages


# unsupported inputs must publish failure instead of becoming partial model context or blocking later selection
def IsContextReady(
    RepoName: str,
    Evidence: dict[str, object],
    PullData: dict[str, object],
    Settings: dict[str, object],
    RequestId: int | None,
) -> bool:
    FileList = ReadPages(f"repos/{RepoName}/pulls/{Evidence['pull_number']}/files")
    if len(FileList) != PullData["changed_files"]:
        raise ValueError("Changed file inventory is incomplete")
    try:
        Content = BuildContext(Evidence, PullData, FileList, Settings, RequestId)
    except ValueError as ErrorInfo:
        ApiCall(
            f"repos/{RepoName}/check-runs",
            {
                "name": Settings["CheckName"],
                "head_sha": Evidence["head_sha"],
                "external_id": str(Evidence["review_id"]),
                "status": "completed",
                "conclusion": "failure",
                "output": {
                    "title": "Review input exceeds supported bounds",
                    "summary": str(ErrorInfo)
                    + (
                        f"\n\nMention comment: {RequestId}"
                        if RequestId is not None
                        else ""
                    )
                    + f"\n\nReview snapshot: {Evidence['review_id']}",
                },
            },
        )
        return False
    Path("ReviewInput/Context.json").write_text(Content)
    return True
