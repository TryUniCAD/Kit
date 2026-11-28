from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath

from pytest import approx as NearValue, mark as MarkTests

from convert import open_document as OpenDocument
from tests.Convert.Api.Fusion.SavedCuboid.LabelSavedParam import LabelSavedParam
from tests.Convert.Api.Fusion.SavedCuboid.ReadParamRoles import ReadParamRoles
from tests.Convert.Api.Fusion.SavedCuboid.ReadParamSem import ReadParamSem
from tests.Convert.Api.Fusion.SavedCuboid.RunParamStage import RunParamStage
from tests.Convert.Api.Fusion.SavedCuboid.SavedCase import SavedCase
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource


# a fresh writer must preserve the saved parameter roster when its source path is absent
@MarkTests.parametrize(
    "CaseValue,AddLabels",
    ((KSavedCases[0], False), (KSavedCases[1], False), (KSavedCases[1], True)),
)
def TestSavedParams(TmpPath: FilePath, CaseValue: SavedCase, AddLabels: bool) -> None:
    Payload = SavedSource(CaseValue).read_bytes()
    assert HashBytes(Payload).hexdigest() == CaseValue.DigestValue
    if AddLabels:
        Payload = LabelSavedParam(Payload)
    Source = TmpPath / "Original.f3d"
    _ = Source.write_bytes(Payload)
    Before = OpenDocument(Payload, source_format="f3d")
    if AddLabels:
        assert any(
            Param.attributes["native_name"] == "Extrusion height label"
            and Param.attributes["comment"] == "Shop note"
            for Param in Before.parameters
        )
    Replay = TmpPath / "Replay"
    Replay.mkdir()
    Request = Replay / "Request.json"
    Prepare = RunParamStage("PrepareRequest.py", Source, Request)
    assert Prepare.returncode == 0, Prepare.stderr
    _ = Source.replace(TmpPath / "Retained.f3d")
    assert not Source.exists() and tuple(Replay.iterdir()) == (Request,)
    Candidate = Replay / "Candidate.f3d"
    Generate = RunParamStage("GenerateSavedCuboid.py", Request, Candidate)
    assert Generate.returncode == 0, Generate.stderr
    After = OpenDocument(Candidate.read_bytes(), source_format="f3d")
    assert len(After.parameters) == len(Before.parameters) == 7
    assert ReadParamSem(After) == ReadParamSem(Before)
    assert ReadParamRoles(After) == ReadParamRoles(Before)
    assert After.configurations[0].name == Before.configurations[0].name
    assert After.metadata["fusion.read_only"] is True
    assert After.bodies[0].topology.volume == NearValue(
        Before.bodies[0].topology.volume
    )
