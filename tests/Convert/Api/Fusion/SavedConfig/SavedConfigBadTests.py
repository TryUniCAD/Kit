from dataclasses import replace as ReplaceData
from pathlib import Path as FilePath

from convert.Formats.Fusion.ContainerCodec.EmitContainer import EmitContainer
from convert.Formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from tests.Convert.Api.Fusion.SavedCuboid.RunParamStage import RunParamStage
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource


# a populated configuration source must fail before a portable request can be published
def TestConfigData(TmpPath: FilePath) -> None:
    Native = ReadContainer(SavedSource(KSavedCases[0]).read_bytes())
    Parts = tuple(
        (
            ReplaceData(Entry, Payload=b'{"variants":["large"]}')
            if Entry.Name.endswith(".dsgcfg")
            else Entry
        )
        for Entry in Native.Parts
    )
    Source = TmpPath / "Original.f3d"
    _ = Source.write_bytes(EmitContainer(ReplaceData(Native, Parts=Parts)))
    Request = TmpPath / "Request.json"
    Prepare = RunParamStage(
        "PrepareRequest.py", Source, Request, ResearchFolder="SavedConfigEnvelope"
    )
    assert Prepare.returncode == 1 and not Request.exists()
    assert "Nonempty Fusion configurations require a qualified schema" in Prepare.stderr
