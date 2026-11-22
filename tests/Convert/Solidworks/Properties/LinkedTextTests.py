from dataclasses import replace as ReplaceValue
from io import BytesIO as ByteBuffer
from re import escape as EscapeRegex

from pytest import raises as ExpectError

from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from tests.Convert.Commands.WrapDocument import WrapDocument
from tests.Convert.Solidworks.Properties.RunPartText import KPartCorpus
from tests.Convert.Solidworks.Properties.WriteTextTests import KPartCause


# an otherwise valid assembly write must account for its actual linked native part status
def TestLinkedText() -> None:
    PartValue = OpenDocument(
        KPartCorpus / "ladder/L1_boss.SLDPRT",
        source_format="solidworks.sldprt",
        include_tessellation=False,
    )
    Wrapped = WrapDocument(PartValue)
    assert Wrapped.assembly is not None
    AssemblyValue = ReplaceValue(
        Wrapped,
        assembly=ReplaceValue(Wrapped.assembly, mates=(), mate_entities=()),
    )
    AssemblyValue.assert_valid()
    MessageValue = (
        f"SOLIDWORKS part text properties are unavailable for writing ({KPartCause})"
    )
    Target = ByteBuffer(b"unchanged")
    with ExpectError(ValueError, match=EscapeRegex(MessageValue)):
        _ = WriteDocument(AssemblyValue, Target, destination_format="interchange.json")
    assert Target.getvalue() == b"unchanged" and Target.tell() == 0
