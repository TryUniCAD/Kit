from io import BytesIO as ByteStream
from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as MarkTests
from pytest import raises as Raises

from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from convert.adapters.base.UsabilityError import UsabilityError

# these generated archives and receipts are retained from the controlled vendor runs
KMeasureRoot = FilePath(__file__).resolve().parents[4] / "re/Fusion/WriterMeasurement"


# a strict sdk publication must reproduce the measured bytes and attest both native outcomes
@MarkTests.parametrize("RoleText", ("reconstruction", "edited"))
def TestFusePublish(RoleText: str, TmpPath: FilePath) -> None:
    Source = KMeasureRoot / f"{RoleText}.f3d"
    Receipt = LoadJson((KMeasureRoot / f"{RoleText}-receipt.json").read_bytes())
    Document = OpenDocument(Source)
    Target = TmpPath / "Published.f3d"
    Result = WriteDocument(
        Document,
        Target,
        allow_carrier=False,
        values={"fusion_native_measurement": Receipt},
    )
    assert Result.vendor_loadable and Result.application_usable
    assert Result.dropped == frozenset()
    assert Target.read_bytes() == Source.read_bytes()


# contradictory or missing evidence must leave a caller stream untouched on strict writes
@MarkTests.parametrize("CaseText", ("missing", "digest", "driver", "edit", "reopen"))
def TestFuseRefuse(CaseText: str) -> None:
    Source = KMeasureRoot / "edited.f3d"
    Receipt = LoadJson((KMeasureRoot / "edited-receipt.json").read_bytes())
    Edits = Receipt["candidate"]["edits"]
    if CaseText == "digest":
        Receipt["candidate_sha256"] = "0" * 64
    if CaseText == "driver":
        Edits[0]["parameter"] = "kitWidth"
    if CaseText == "edit":
        Edits[0]["edited_value"] += 0.1
    if CaseText == "reopen":
        Edits[0]["reopen_pid"] = Receipt["candidate"]["pid"]
    Target = ByteStream(b"existing output")
    ErrorType = UsabilityError if CaseText == "missing" else ValueError
    Values = {} if CaseText == "missing" else {"fusion_native_measurement": Receipt}
    with Raises(ErrorType):
        _ = WriteDocument(
            OpenDocument(Source),
            Target,
            destination_format="f3d",
            allow_carrier=False,
            values=Values,
        )
    assert Target.getvalue() == b"existing output" and Target.tell() == 0


# even a matching measurement cannot attest an archive embedded in a larger stream
def TestFuseExtent() -> None:
    Source = KMeasureRoot / "edited.f3d"
    Receipt = LoadJson((KMeasureRoot / "edited-receipt.json").read_bytes())
    Target = ByteStream(b"existing output")
    with Raises(ValueError, match="empty"):
        _ = WriteDocument(
            OpenDocument(Source),
            Target,
            destination_format="f3d",
            allow_carrier=False,
            values={"fusion_native_measurement": Receipt},
        )
    assert Target.getvalue() == b"existing output" and Target.tell() == 0
