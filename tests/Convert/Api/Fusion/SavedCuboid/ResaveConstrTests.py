from os import environ as SystemEnv
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath

from pytest import approx as NearValue

from convert import open_document as OpenDocument
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument


# a fresh ordinary authoring process must load the inherited parameter schemas on its own
def TestCuboidEmit(TmpPath: FilePath) -> None:
    Repository = FilePath(__file__).resolve().parents[5]
    Target = TmpPath / "Ordinary.f3d"
    Program = (
        "from pathlib import Path\n"
        "from sys import argv\n"
        "from convert import write_document\n"
        "from convert.adapters.Fusion import MakeFusionDoc\n"
        "from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec\n"
        "spec = DocumentSpec('Standalone owner', 'height', 15.2, ProfileKind='cuboid',"
        " ConstrainRectangle=True, WidthMm=19.1, DepthMm=22.2)\n"
        "write_document(MakeFusionDoc(spec), Path(argv[1]), destination_format='f3d',"
        " allow_carrier=False)\n"
    )
    Result = RunProcess(
        (KPythonPath, "-B", "-c", Program, str(Target)),
        cwd=TmpPath,
        env={**SystemEnv, "PYTHONPATH": str(Repository / "src")},
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Result.returncode == 0, Result.stdout + Result.stderr
    Model = ReadDocument(Target.read_bytes())
    assert len(Model.Bodies) == 1
    Document = OpenDocument(Target, strict=True)
    assert not Document.diagnostics and not Document.brep_payloads
    assert Document.bodies[0].topology.volume == NearValue(19.1 * 22.2 * 15.2)
    assert len(Document.parameters) == 7 and len(Document.feature_timeline) == 2
