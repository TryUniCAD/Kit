from hashlib import sha256 as DigestBytes
from json import loads as ParseJson
from subprocess import run as RunProcess
from sys import executable as PythonExe

from interchange.document.Models.DocumentModel import CadDocument
from tests.Research.Archives.Comparison.SemanticComparisonTests import KRepoRoot

# the discovery capture provides a stable source independent of comparator rules
KSourceSha = "db1390476325f5817e6f80fb4067a3c6df5cc063315604c133ccbeaafdeac357"


# the public decoder must supply the actual strict graph for both comparison inputs
def ReadSketchPart() -> CadDocument:
    SourcePath = (
        KRepoRoot
        / "re/automation/PairedCaptures/P03/solidworks-db1390476325"
        / "P03-solidworks-baseline-a.SLDPRT"
    )
    assert DigestBytes(SourcePath.read_bytes()).hexdigest() == KSourceSha
    Process = RunProcess(
        (
            PythonExe,
            "-B",
            "-m",
            "KitCli",
            "decode",
            str(SourcePath),
            "--from",
            "solidworks.sldprt",
        ),
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Process.returncode == 0, Process.stdout + Process.stderr
    Document = CadDocument.from_dict(ParseJson(Process.stdout)["document"])
    assert Document.source.sha256 == KSourceSha
    return Document
