from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe

from interchange.document.Models.DocumentModel import CadDocument
from tests.Research.Archives.Comparison.SemanticComparisonTests import KRepoRoot

# a fresh public api read supplies the actual generated native ownership and span
KDecodeAxis = """
import sys
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1]) / "src"))
from convert import open_document as OpenDocument

# the generated cache free archive must decode through the strict design option
KDocument = OpenDocument(
    Path(sys.argv[2]),
    source_format="solidworks.sldprt",
    include_brep=False,
    include_tessellation=False,
    strict=True,
)
sys.stdout.buffer.write(KDocument.to_json().encode("utf-8"))
"""


# the ordinary strict design read retains its typed neutral data through stdout
def DecodeAxis(NativePath: FilePath) -> CadDocument:
    Result = RunProcess(
        [PythonExe, "-I", "-B", "-c", KDecodeAxis, str(KRepoRoot), str(NativePath)],
        cwd=NativePath.parent,
        capture_output=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    assert Result.returncode == 0, Result.stderr
    return CadDocument.from_json(Result.stdout)
