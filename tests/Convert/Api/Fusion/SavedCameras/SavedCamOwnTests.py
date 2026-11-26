from pathlib import Path as FilePath

from convert import open_document as OpenDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField
from tests.Convert.Api.Fusion.SavedCuboid.RunParamStage import RunParamStage
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource


# a retained shared camera must refuse scoped projection even when strict readback keeps it
def TestSharedCam(TmpPath: FilePath) -> None:
    Native = ReadDocument(SavedSource(KSavedCases[0]).read_bytes())
    Views = BuildGraph(Native).ByClass("NamedView")
    Shared = ChangeField(
        Native, Views[1].ObjectId, "m_rCamera", Views[0].Fields["m_rCamera"]
    )
    Payload = EmitParsed(Shared)
    assert (
        OpenDocument(Payload, source_format="f3d").metadata["fusion.read_only"] is True
    )
    Source = TmpPath / "Original.f3d"
    _ = Source.write_bytes(Payload)
    Request = TmpPath / "Request.json"
    Prepare = RunParamStage(
        "PrepareRequest.py", Source, Request, ResearchFolder="SavedCameras"
    )
    assert Prepare.returncode == 1 and not Request.exists()
    assert Prepare.stderr.strip() == (
        "Saved cuboid named-camera request refused: Named camera is shared or belongs to a foreign graph"
    )
