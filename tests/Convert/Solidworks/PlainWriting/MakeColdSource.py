from hashlib import sha256 as CalcSha
from io import BytesIO
from pathlib import Path as FilePath

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from tests.Convert.Solidworks.PlainWriting.MeasurePlainDoc import MeasurePlainDoc


# measured neutral controls supply regenerated source bytes rather than a captured template
def MakeColdSource(
    Folder: FilePath, RoleName: str
) -> tuple[FilePath, dict[str, object], str, str]:
    Document, Envelope, Digest = MeasurePlainDoc(RoleName)
    NameValue = f"{Document.metadata['name']}.SLDPRT"
    Candidate = PrepareNative(
        Document,
        BytesIO(),
        1794973072,
        WriteOptions(values={"final_destination": rf"C:\KitSdkCandidates\{NameValue}"}),
    )
    assert CalcSha(Candidate.BytesValue).hexdigest() == Digest
    Source = Folder / "Source.SLDPRT"
    _ = Source.write_bytes(Candidate.BytesValue)
    return Source, Envelope, Digest, NameValue
