from pathlib import Path


# trusted policy is stored in actual git blobs rather than supplied through a mocked reader
def WritePolicies(RootPath: Path, CaseName: str) -> None:
    Content = (
        "p" * 151000
        if CaseName == "policy"
        else "Authored context compatibility policy\n"
    )
    for FileName in (
        "AGENTS.md",
        "Roadmap.md",
        ".agents/skills/standard-pr-practice/SKILL.md",
        "Documentation/Planning/Generated/Tasks.md",
        "Documentation/Planning/Generated/Deliveries.md",
        "Documentation/Reference/Operations/CadSuccessCriteria.md",
    ):
        FilePath = RootPath / FileName
        FilePath.parent.mkdir(parents=True, exist_ok=True)
        WriteCount = FilePath.write_text(Content, encoding="utf-8", newline="\n")
        assert WriteCount == len(Content)


# all three revisions have independent content while negative fixtures cross real blob boundaries
def WriteSources(
    RootPath: Path, FileCount: int, Marker: str, CaseName: str
) -> tuple[str, ...]:
    FileNames: list[str] = []
    for Index in range(FileCount):
        FileName = f"Source{Index:02d}.txt"
        RowCount = 2 if CaseName == "count" else 700
        Payload = (f"{Marker}{Index:03d}abcde\n" * RowCount).encode()
        if Index == 0 and CaseName == "oversized":
            Payload = Marker.encode() * 160001
        if Index == 0 and CaseName == "binary":
            Payload = b"\0" + Marker.encode()
        WriteCount = (RootPath / FileName).write_bytes(Payload)
        assert WriteCount == len(Payload)
        FileNames.append(FileName)
    return tuple(FileNames)
