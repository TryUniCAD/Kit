from pathlib import Path as FilePath

from convert import open_document as OpenDocument
from tests.Convert.Api.Fusion.SavedConfig.AliasConfigPart import AliasConfigPart
from tests.Convert.Api.Fusion.SavedCuboid.RunParamStage import RunParamStage
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource


# shared table and rule identifiers must fail before scoped request publication
def TestConfigAlias(TmpPath: FilePath) -> None:
    Payload = AliasConfigPart(SavedSource(KSavedCases[0]).read_bytes())
    assert (
        OpenDocument(Payload, source_format="f3d").metadata["fusion.read_only"] is True
    )
    Source = TmpPath / "Original.f3d"
    _ = Source.write_bytes(Payload)
    Request = TmpPath / "Request.json"
    Prepare = RunParamStage(
        "PrepareRequest.py", Source, Request, ResearchFolder="SavedConfigEnvelope"
    )
    assert Prepare.returncode == 1 and not Request.exists()
    assert Prepare.stderr.strip() == (
        "Saved cuboid empty configuration request refused: Configuration table and rule share an identity"
    )
