from hashlib import sha256 as DigestBytes
from json import dumps as EncodeJson, loads as ParseJson
from os import environ as Environment, pathsep as PathSep
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe
from typing import cast as CastValue

from pytest import mark as MarkValue

from interchange.document.Models.DocumentModel import CadDocument
from tests.Research.Archives.FreeCadAliases.MakePadFixture import MakePadFixture

# child processes must load the same native decoder as the public registry
KRepoRoot = FilePath(__file__).resolve().parents[4]


# exact source ownership and the saved length must agree before the dependency is exposed
@MarkValue.parametrize(
    "CaseName", ("native", "stale", "label", "duplicate", "subelement")
)
def CheckPadExpr(TmpPath: FilePath, CaseName: str) -> None:
    SourcePath = TmpPath / "LocalSketch.FCStd"
    Payload = MakePadFixture(CaseName)
    assert SourcePath.write_bytes(Payload) == len(Payload)
    Process = RunProcess(
        [PythonExe, "-B", "-P", "-m", "tests.Research.Archives.FreeCadNativeEndTests"],
        cwd=TmpPath,
        env={
            **Environment,
            "PYTHONPATH": PathSep.join((str(KRepoRoot), str(KRepoRoot / "src"))),
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Process.returncode == 0, Process.stderr + Process.stdout
    assert SourcePath.read_bytes() == Payload
    Report = CastValue(dict[str, object], ParseJson(Process.stdout))
    assert Report["input_sha256"] == DigestBytes(Payload).hexdigest()
    Document = CadDocument.from_json(EncodeJson(Report["document"]))
    (SketchValue,) = Document.sketches
    (Feature,) = Document.feature_timeline
    (DepthValue,) = (
        Value for Value in Document.parameters if Value.owner_id == Feature.id
    )
    assert DepthValue.id == "freecad:parameter:Boss:Length"
    assert DepthValue.value.value == (17.0 if CaseName == "stale" else 16.0)
    assert DepthValue.value.unit == "mm"
    assert DepthValue.expression is not None
    ObjectName = "Caption" if CaseName == "label" else "Layout"
    assert DepthValue.expression.source == f"{ObjectName}.Constraints.span / 3"
    if CaseName == "native":
        (RuleValue,) = SketchValue.constraints
        ParamId = "freecad:parameter:Layout:constraint:0"
        assert RuleValue.parameter_id == ParamId
        assert DepthValue.expression.parameter_ids == (ParamId,)
    else:
        assert not DepthValue.expression.parameter_ids
