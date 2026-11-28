from typing import cast
from urllib.parse import quote

from ObjectMap import ObjectMap
from Publication.SafeText import SafeText


# priority grouping makes actionable defects easy to scan without burying lower priority findings
def FormatFindings(Report: dict[str, object], Context: dict[str, object]) -> str:
    Findings = [ObjectMap(Entry) for Entry in cast(list[object], Report["findings"])]
    if not Findings:
        return "### Findings\n\nNo findings reported."
    Sections = ["### Findings"]
    RepoName = quote(str(Context["repository_name"]), safe="/")
    SourceStatus = {
        str(ObjectMap(Entry)["path"]): ObjectMap(Entry)["status"]
        for Entry in cast(list[object], Context["files"])
    }
    for Priority in ("P1", "P2", "P3"):
        Matches = [Finding for Finding in Findings if Finding["priority"] == Priority]
        if not Matches:
            continue
        Sections.append(f"#### {Priority}")
        for Finding in Matches:
            TitleText = SafeText(Finding["title"]).replace("\n", " ")
            FileName = SafeText(Finding["path"]).replace("\n", " ")
            Revision = (
                ObjectMap(Context["evidence"])["merge_base_sha"]
                if SourceStatus.get(str(Finding["path"])) == "removed"
                else Report["head"]
            )
            SourceLink = f"https://github.com/{RepoName}/blob/{Revision}/{quote(str(Finding['path']), safe='/')}#L{Finding['line']}"
            Sections.append(
                f"**{TitleText}**\n\n[`{FileName}:{Finding['line']}`]({SourceLink})\n\n{SafeText(Finding['body'])}"
            )
    return "\n\n".join(Sections)
