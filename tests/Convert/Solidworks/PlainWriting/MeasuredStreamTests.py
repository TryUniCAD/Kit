from hashlib import sha256 as CalcSha
from io import BytesIO
from pathlib import Path as FilePath
from types import SimpleNamespace as SinkNamespace
from typing import cast as CastValue

from pytest import raises as RaisesError

from convert.api import open_document as OpenDocument, write_document as WriteDocument
from convert.adapters.base.ContractTypes import BinaryWriter
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Solidworks.PlainWriting.MeasurePlainDoc import MeasurePlainDoc


# both real entry paths use the same measured locator and complete caller supplied receipt
def SendMeasured(
    Document: CadDocument,
    Target: BinaryWriter,
    Envelope: dict[str, object],
    IsDirect: bool,
) -> WriteResult:
    NameValue = CastValue(str, Document.metadata["name"])
    Options = {
        "final_destination": rf"C:\KitSdkCandidates\{NameValue}.SLDPRT",
        KPartMeasureOpt: Envelope,
    }
    if IsDirect:
        return SldprtWriter().write(Document, Target, WriteOptions(values=Options))
    return WriteDocument(
        Document,
        Target,
        destination_format=KPartFormatId,
        allow_carrier=False,
        values=Options,
    )


# a prefix stale tail or displaced cursor must never receive measured bytes or native acceptance
def TestSinkBounds() -> None:
    Document, Envelope, Digest = MeasurePlainDoc("Skew")
    for IsDirect in (False, True):
        for Original, Position in ((b"previous content", 0), (b"prefix", 6), (b"", 12)):
            Target = BytesIO(Original)
            _ = Target.seek(Position)
            with RaisesError(ValueError, match="empty seekable binary stream"):
                _ = SendMeasured(Document, Target, Envelope, IsDirect)
            assert Target.getvalue() == Original and Target.tell() == Position
        Buffered = BytesIO()
        Unseekable = CastValue(BinaryWriter, SinkNamespace(write=Buffered.write))
        with RaisesError(ValueError, match="empty seekable binary stream"):
            _ = SendMeasured(Document, Unseekable, Envelope, IsDirect)
        assert Buffered.getvalue() == b""
        EmptySink = BytesIO()
        Outcome = SendMeasured(Document, EmptySink, Envelope, IsDirect)
        assert Outcome.vendor_loadable and Outcome.application_usable
        assert CalcSha(EmptySink.getvalue()).hexdigest() == Digest


# a writable file stream needs only cursor operations before emitting the measured bytes
def TestFileSink(TmpPath: FilePath) -> None:
    Document, Envelope, Digest = MeasurePlainDoc("Step")
    for IsDirect in (False, True):
        TargetPath = TmpPath / f"output-{IsDirect}.SLDPRT"
        with TargetPath.open("wb") as OutputFile:
            assert not OutputFile.readable() and OutputFile.seekable()
            Outcome = SendMeasured(Document, OutputFile, Envelope, IsDirect)
            assert Outcome.vendor_loadable and Outcome.application_usable
        assert CalcSha(TargetPath.read_bytes()).hexdigest() == Digest


# writers without standalone attestation retain their ordinary binary append boundary
def TestAppendJson() -> None:
    Document, _, _ = MeasurePlainDoc("Skew")
    Prefix = b"prior generic stream data\n"
    Target = BytesIO(Prefix)
    _ = Target.seek(len(Prefix))
    _ = WriteDocument(Document, Target, destination_format="interchange.json")
    Written = Target.getvalue()
    assert Written.startswith(Prefix)
    assert (
        OpenDocument(Written[len(Prefix) :], source_format="interchange.json")
        == Document
    )
