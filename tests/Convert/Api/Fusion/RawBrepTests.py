from pathlib import Path as FilePath

from convert import extract_brep as ExtractBrep, write_document as WriteDocument
from tests.Convert.Api.Fusion.AdapterCases import AdapterCase
from tests.Convert.Formats.JsonTests import NonSeekable


# strict extraction must accept a qualified fusion source without detached payloads
def TestFusionBrep(TmpPath: FilePath) -> None:
    Archive = TmpPath / "Parameter.f3d"
    _ = WriteDocument(
        AdapterCase("parameter"),
        Archive,
        destination_format="fusion.f3d",
        allow_carrier=False,
    )
    Source = NonSeekable(Archive.read_bytes())
    assert ExtractBrep(Source, TmpPath / "payloads", source_format="fusion.f3d") == ()
    assert Source.IsConsumed
