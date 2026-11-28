# failed input preparation still needs trusted metadata for native reporting and reaction cleanup
def MakeContext(
    Evidence: dict[str, object],
    PullData: dict[str, object],
    Settings: dict[str, object],
    RequestId: int | None,
) -> dict[str, object]:
    return {
        "evidence": Evidence,
        "title": PullData["title"],
        "body": PullData["body"],
        "mention_comment": RequestId,
        "review_runtime": {
            "model": Settings["Model"],
            "reasoning_effort": Settings["ReasoningEffort"],
        },
        "policy_sha": Settings["PolicyRevision"],
        "input_complete": False,
        "changed_file_count": PullData["changed_files"],
        "files": [],
    }
