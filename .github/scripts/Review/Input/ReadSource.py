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
