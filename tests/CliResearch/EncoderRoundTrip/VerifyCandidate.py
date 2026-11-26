from hashlib import sha256 as HashContent
from pathlib import Path as FilePath

from convert.api.ApiOpen import OpenDocument
from tests.CliResearch.EncoderRoundTrip.VerifyDrive import VerifyDrive
from tests.CliResearch.EncoderRoundTrip.VerifyGeometry import VerifyGeometry


# strict artifact reads must connect recorded candidate custody to independently expected driving geometry
def VerifyCandidate(
    NativePath: FilePath,
    Dimensions: tuple[float, float, float],
    ExpectedHash: str,
) -> None:
    assert HashContent(NativePath.read_bytes()).hexdigest() == ExpectedHash
    Document = OpenDocument(NativePath, SourceFormat="fusion.f3d", StrictMode=True)
    VerifyDrive(Document, Dimensions[2])
    VerifyGeometry(Document, Dimensions)
