import subprocess as ProcessTools


# git object reads avoid checking out or executing proposed repository code
def ReadSource(Revision: str, FileName: str) -> str:
    if len(Revision) != 40 or any(
        Letter not in "0123456789abcdef" for Letter in Revision
    ):
        raise ValueError("Invalid source revision")
    Result = ProcessTools.run(
        ["git", "show", f"{Revision}:{FileName}"],
        capture_output=True,
        check=True,
        timeout=30,
    )
    if len(Result.stdout) > 160000 or b"\0" in Result.stdout:
        raise ValueError(
            "Changed content requires a separate binary or large file review"
        )
    return Result.stdout.decode("utf-8")


# complete changed sources and their previous versions expose more than truncated patch snippets
def CollectFiles(
    Files: list[dict[str, object]], Evidence: dict[str, object]
) -> list[dict[str, object]]:
    if len(Files) > 40:
        raise ValueError("PR exceeds the complete review file limit")
    Sources: list[dict[str, object]] = []
    for Entry in Files:
        FileName = str(Entry["filename"])
        Sources.append(
            {
                "path": FileName,
                "patch": Entry.get("patch"),
                "before": (
                    ""
                    if Entry["status"] == "added"
                    else ReadSource(
                        str(Evidence["base_sha"]),
                        str(Entry.get("previous_filename", FileName)),
                    )
                ),
                "after": (
                    ""
                    if Entry["status"] == "removed"
                    else ReadSource(str(Evidence["head_sha"]), FileName)
                ),
            }
        )
    return Sources
