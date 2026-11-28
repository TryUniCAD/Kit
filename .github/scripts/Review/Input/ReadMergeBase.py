from ApiCall import ApiCall
from ObjectMap import ObjectMap


# proposed diffs must use their merge base rather than attribute concurrent target edits to the author
def ReadMergeBase(RepoName: str, Evidence: dict[str, object]) -> object:
    Comparison = ObjectMap(
        ApiCall(
            f"repos/{RepoName}/compare/{Evidence['base_sha']}...{Evidence['head_sha']}?per_page=1"
        )
    )
    return ObjectMap(Comparison["merge_base_commit"])["sha"]
