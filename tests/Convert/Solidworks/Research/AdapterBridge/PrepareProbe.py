from io import BytesIO
from pathlib import Path as FilePath

from convert import write_document as WriteDoc
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from interchange.document.Models.DocumentModel import CadDocument


# this neutral probe must reach the real measurement gate before either caller destination changes
def CheckProbeGate(Document: CadDocument, TargetPath: FilePath) -> None:
    assert not TargetPath.exists()
    HadParent = TargetPath.parent.exists()
    PriorPaths: set[FilePath] = set(TargetPath.parent.iterdir()) if HadParent else set()
    PriorBytes = b"prior output"
    StreamValue = BytesIO(PriorBytes)
    for Destination in (TargetPath, StreamValue):
        try:
            _ = WriteDoc(
                Document,
                Destination,
                destination_format=KPartFormatId,
                allow_carrier=False,
                values={
                    "final_destination": str(TargetPath),
                    "require_native_transfers": True,
                },
            )
        except ValueError as ErrorValue:
            assert "offline native measurement receipt" in str(ErrorValue)
        else:
            raise AssertionError("unmeasured probe reached publication")
    assert not TargetPath.exists() and TargetPath.parent.exists() == HadParent
    if HadParent:
        assert set(TargetPath.parent.iterdir()) == PriorPaths
    assert StreamValue.getvalue() == PriorBytes and StreamValue.tell() == 0


# an explicit authoring event keeps both internal preparation routes deterministic without qualifying the probe
def PrepareProbe(Document: CadDocument, TargetPath: FilePath, WrittenAt: int) -> bytes:
    CheckProbeGate(Document, TargetPath)
    PathPart = PrepareNative(Document, TargetPath, WrittenAt)
    StreamValue = BytesIO()
    StreamPart = PrepareNative(
        Document,
        StreamValue,
        WrittenAt,
        WriteOptions(values={"final_destination": str(TargetPath)}),
    )
    assert not TargetPath.exists() and StreamValue.getvalue() == b""
    RawValue = StreamPart.BytesValue
    assert RawValue and PathPart.BytesValue == RawValue
    TargetPath.parent.mkdir(parents=True, exist_ok=True)
    with TargetPath.open("xb") as OutputFile:
        WrittenSize = OutputFile.write(PathPart.BytesValue)
        assert WrittenSize == len(RawValue)
    return RawValue
