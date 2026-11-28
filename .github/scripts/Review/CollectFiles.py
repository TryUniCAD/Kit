from Input.ReadSource import ReadSource
from Input.ReadTarget import ReadTarget


# complete changed sources and their previous versions expose more than truncated patch snippets
def CollectFiles(
    Files: list[dict[str, object]], Evidence: dict[str, object]
) -> list[dict[str, object]]:
    Sources: list[dict[str, object]] = []
    for Entry in Files[:40]:
        FileName = str(Entry["filename"])
        try:
            Source = {
                "path": FileName,
                "status": Entry["status"],
                "patch": (
                    Entry.get("patch")
                    if len(str(Entry.get("patch", ""))) <= 40000
                    else None
                ),
                "before": (
                    ""
                    if Entry["status"] == "added"
                    else ReadSource(
                        str(Evidence["merge_base_sha"]),
                        str(Entry.get("previous_filename", FileName)),
                    )
                ),
                "after": (
                    ""
                    if Entry["status"] == "removed"
                    else ReadSource(str(Evidence["head_sha"]), FileName)
                ),
                "target": ReadTarget(
                    str(Evidence["base_sha"]),
                    str(Entry.get("previous_filename", FileName)),
                ),
            }
        except (ValueError, ProcessTools.CalledProcessError) as ErrorInfo:
            Source = {
                "path": FileName,
                "status": Entry["status"],
                "before": None,
                "after": None,
                "target": None,
                "patch": (
                    Entry.get("patch")
                    if len(str(Entry.get("patch", ""))) <= 40000
                    else None
                ),
                "omitted": str(ErrorInfo),
            }
        Sources.append(Source)
    return Sources


import subprocess as ProcessTools
