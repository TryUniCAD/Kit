from collections.abc import Mapping
from hashlib import sha256 as CalcSha
from pathlib import Path as FilePath, PureWindowsPath

from convert import open_document as OpenDocument, write_document as WriteDocument


# the measured bundle must republish from a normal strict reader with actual local paths
def VerifyReplay(
    Directory: FilePath,
    NativePath: PureWindowsPath,
    Measurement: Mapping[str, object],
    Expected: Mapping[str, str],
) -> None:
    for NameValue in Expected:
        Member = Directory / NameValue
        _ = Member.rename(Member.with_suffix(Member.suffix.lower()))
    SourcePath = Directory / NativePath.with_suffix(NativePath.suffix.lower()).name
    Document = OpenDocument(SourcePath)
    Original = Document.to_json()
    OutFolder = Directory / "Reopened"
    OutFolder.mkdir()
    Result = WriteDocument(
        Document,
        OutFolder / NativePath.name,
        allow_carrier=False,
        values={
            "native_destination": str(NativePath),
            "require_native_transfers": True,
            "solidworks_native_measurement": Measurement,
        },
    )
    assert Result.application_usable and Result.vendor_loadable and not Result.dropped
    assert Document.to_json() == Original
    assert {
        Member.name: CalcSha(Member.read_bytes()).hexdigest()
        for Member in OutFolder.iterdir()
    } == Expected
