from io import BytesIO

from pytest import mark as MarkTests, raises as RaisesError

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.adapters.registry.RegistryErrors import AdapterNotFoundError
from tests.Convert.Integration.Fusion.DualSide.Admission.ReadAdmitCases import (
    ReadAdmitCases,
)


# read only source admission cannot become native output or interchange export by accident
@MarkTests.parametrize("CaseName", ("baseline", "holdout_b", "holdout_b_restored"))
@MarkTests.parametrize("FormatName", ("fusion.f3d", "interchange.json"))
def CheckDualWrite(CaseName: str, FormatName: str) -> None:
    Sample = next(Value for Value in ReadAdmitCases() if Value.Identity == CaseName)
    Document = OpenDocument(Sample.Source, strict=True)
    Target = BytesIO()
    RejectType = AdapterNotFoundError if FormatName == "fusion.f3d" else ValueError
    with RaisesError(RejectType):
        _ = WriteDocument(Document, Target, destination_format=FormatName)
    assert Target.getvalue() == b""
