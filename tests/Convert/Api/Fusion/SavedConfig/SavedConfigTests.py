from hashlib import sha256 as HashBytes
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from pytest import mark as MarkTests

from convert import open_document as OpenDocument
from tests.Convert.Api.Fusion.SavedCameras.ReadCamViews import ReadCamViews
from tests.Convert.Api.Fusion.SavedConfig.ReadConfigRoles import ReadConfigRoles
from tests.Convert.Api.Fusion.SavedCuboid.ReadParamSem import ReadParamSem
from tests.Convert.Api.Fusion.SavedCuboid.RunParamStage import RunParamStage
from tests.Convert.Api.Fusion.SavedCuboid.SavedCase import SavedCase
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource


# fresh generation must retain explicit envelope roles without importing source identifiers
@MarkTests.parametrize(
    "CaseValue,Expected",
    (
        (KSavedCases[0], ("table", "rule")),
        (KSavedCases[1], ("rule", "table")),
        (KSavedCases[1], ()),
    ),
)
def TestSavedConfig(
    TmpPath: FilePath, CaseValue: SavedCase, Expected: tuple[str, ...]
) -> None:
    Payload = SavedSource(CaseValue).read_bytes()
    assert HashBytes(Payload).hexdigest() == CaseValue.DigestValue
    Known = ReadConfigRoles(Payload)
    Source = TmpPath / "Original.f3d"
    _ = Source.write_bytes(Payload)
    Replay = TmpPath / "Replay"
    Replay.mkdir()
    Request = Replay / "Request.json"
    Prepare = RunParamStage(
        "PrepareRequest.py", Source, Request, ResearchFolder="SavedConfigEnvelope"
    )
    assert Prepare.returncode == 0, Prepare.stderr
    Handoff = CastValue(
        dict[str, object], LoadJson(Request.read_text(encoding="utf-8"))
    )
    assert Handoff["configuration_parts"] == [RoleName for RoleName, _ in Known]
    if not Expected:
        Handoff["configuration_parts"] = []
        _ = Request.write_text(DumpJson(Handoff), encoding="utf-8")
    _ = Source.replace(TmpPath / "Retained.f3d")
    assert not Source.exists() and tuple(Replay.iterdir()) == (Request,)
    Candidate = Replay / "Candidate.f3d"
    Generate = RunParamStage(
        "GenerateSavedCuboid.py",
        Request,
        Candidate,
        ResearchFolder="SavedConfigEnvelope",
    )
    assert Generate.returncode == 0, Generate.stderr
    Generated = Candidate.read_bytes()
    Actual = ReadConfigRoles(Generated)
    assert tuple(RoleName for RoleName, _ in Actual) == Expected
    assert {NameValue for _, NameValue in Actual}.isdisjoint(
        NameValue for _, NameValue in Known
    )
    assert ReadCamViews(Generated) == ReadCamViews(Payload)
    After = OpenDocument(Generated, source_format="f3d")
    assert ReadParamSem(After) == ReadParamSem(
        OpenDocument(Payload, source_format="f3d")
    )
    assert After.metadata["fusion.read_only"] is True
