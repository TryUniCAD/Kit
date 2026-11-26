from pathlib import Path as FilePath

from interchange.document.Models.DocumentModel import CadDocument
from tests.Research.Archives.BossIntent.RunBossIntent import RunIntentStep


# an archived source pin makes the process test independent of local sdk artifacts
def CaptureAxis(TmpPath: FilePath) -> CadDocument:
    SourcePath = TmpPath / "Source.json"
    Result = RunIntentStep(TmpPath, "capture", "--output", str(SourcePath))
    assert Result.returncode == 0, Result.stderr + Result.stdout
    Document = CadDocument.from_json(SourcePath.read_text(encoding="utf-8"))
    assert Document.source.format_id == "solidworks.sldprt"
    assert Document.source.sha256 == (
        "db1390476325f5817e6f80fb4067a3c6df5cc063315604c133ccbeaafdeac357"
    )
    return Document
