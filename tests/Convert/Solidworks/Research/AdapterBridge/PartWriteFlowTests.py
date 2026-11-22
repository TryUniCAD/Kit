from dataclasses import replace as ReplaceValue
from hashlib import sha256 as HashBytes
from io import BytesIO
from math import isclose as IsClose
from pathlib import Path as FilePath
from tempfile import TemporaryDirectory as TempDirectory
from typing import cast as CastValue

from pytest import raises as RaisesError

from convert import open_document as OpenDoc, write_document as WriteDoc
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.serialization.Deserialize import FromData
from tests.Convert.Solidworks.PlainWriting.LeaseMeasPath import LeaseMeasPath
from tests.Convert.Solidworks.PlainWriting.MeasurePlainDoc import MeasurePlainDoc
from tests.Convert.Solidworks.Research.Construction.Part.MakePolygonCase import (
    MakePolygonCase,
)


# the real reader must preserve the generated line loop and its driving feature dimension through its normal entry point
def VerifyPart(
    TargetValue: FilePath | bytes, LineCount: int, DepthValue: float
) -> None:
    ReadValue = OpenDoc(
        TargetValue,
        source_format="solidworks.sldprt",
        include_brep=False,
        include_tessellation=False,
    )
    (SketchValue,) = ReadValue.sketches
    BossValue = ReadValue.feature_timeline[-1]
    assert len(ReadValue.feature_timeline) == 19
    assert len(SketchValue.entities) == LineCount
    assert BossValue.name == "Boss-Extrude1" and BossValue.sketch_id == SketchValue.id
    (ParameterValue,) = tuple(
        Value for Value in ReadValue.parameters if Value.id in BossValue.parameter_ids
    )
    assert ParameterValue.name == "D1" and ParameterValue.owner_id == BossValue.id
    assert IsClose(
        CastValue(float, ParameterValue.value.value), DepthValue, rel_tol=1e-12
    )


# public output must reject unmodeled documents and assembly or drawing destinations without publishing bytes
def VerifyRejects(DocumentValue: CadDocument, TargetPath: FilePath) -> None:
    ExtraValue = ReplaceValue(
        DocumentValue, metadata={"name": TargetPath.stem, "unmapped": 1}
    )
    BeforeValue = TargetPath.read_bytes()
    for InputValue, Destination, FormatId in (
        (ExtraValue, TargetPath, "solidworks.sldprt"),
        (DocumentValue, TargetPath.with_suffix(".SLDASM"), "solidworks.sldasm"),
        (DocumentValue, TargetPath.with_suffix(".SLDDRW"), "solidworks.slddrw"),
    ):
        try:
            _ = WriteDoc(
                InputValue, Destination, destination_format=FormatId, overwrite=True
            )
        except NotFoundError:
            pass
        else:
            raise AssertionError(
                "SOLIDWORKS write accepted an unqualified destination or graph"
            )
    try:
        _ = WriteDoc(DocumentValue, TargetPath)
    except FileExistsError:
        pass
    else:
        raise AssertionError("SOLIDWORKS write silently overwrote the destination")
    assert TargetPath.read_bytes() == BeforeValue
    assert list(TargetPath.parent.iterdir()) == [TargetPath]


# two independently measured designs must publish the exact archive on both ordinary routes
def VerifyMeasured(Folder: FilePath, RoleName: str, LineCount: int) -> None:
    Document, Envelope, Digest = MeasurePlainDoc(RoleName)
    NameValue = f"{Document.metadata['name']}.SLDPRT"
    Policy = {"require_native_transfers": True, KPartMeasureOpt: Envelope}
    with LeaseMeasPath(Folder, NameValue) as TargetPath:
        PathResult = WriteDoc(Document, TargetPath, allow_carrier=False, values=Policy)
        StreamValue = BytesIO()
        StreamResult = WriteDoc(
            Document,
            StreamValue,
            destination_format="SOLIDWORKS.SLDPRT",
            allow_carrier=False,
            values={**Policy, "final_destination": rf"C:\KitSdkCandidates\{NameValue}"},
        )
        Payload = StreamValue.getvalue()
        assert TargetPath.read_bytes() == Payload
        assert HashBytes(Payload).hexdigest() == Digest
        assert PathResult.path == TargetPath.resolve() and StreamResult.path is None
        assert PathResult.bytes_written == StreamResult.bytes_written == len(Payload)
        assert PathResult.application_usable and PathResult.vendor_loadable
        assert StreamResult.application_usable and StreamResult.vendor_loadable
        assert PathResult.native_capabilities == StreamResult.native_capabilities
        assert len(PathResult.native_capabilities) == 6
        DepthValue = CastValue(float, Document.parameters[0].value.value)
        VerifyPart(TargetPath, LineCount, DepthValue)
        VerifyPart(Payload, LineCount, DepthValue)
        VerifyRejects(Document, TargetPath)


# additional authored shapes keep their actual geometry checks and require native evidence for publication
def VerifyUntested(Document: CadDocument, TargetPath: FilePath, LineCount: int) -> None:
    StrictValues = {"require_native_transfers": True}
    OutputValue = BytesIO()
    StreamPolicy = {
        **StrictValues,
        "final_destination": rf"C:\KitSdkCandidates\{TargetPath.name}",
    }
    Candidate = PrepareNative(
        Document, OutputValue, 1794973072, WriteOptions(values=StreamPolicy)
    )
    assert Candidate.BytesValue
    VerifyPart(
        Candidate.BytesValue,
        LineCount,
        CastValue(float, Document.parameters[0].value.value),
    )
    with RaisesError(ValueError, match="offline native measurement receipt"):
        _ = WriteDoc(
            Document,
            OutputValue,
            destination_format="solidworks.sldprt",
            allow_carrier=False,
            values=StreamPolicy,
        )
    PriorBytes = b"previous output"
    _ = TargetPath.write_bytes(PriorBytes)
    with RaisesError(ValueError, match="offline native measurement receipt"):
        _ = WriteDoc(
            Document,
            TargetPath,
            overwrite=True,
            allow_carrier=False,
            values=StrictValues,
        )
    assert TargetPath.read_bytes() == PriorBytes
    assert set(TargetPath.parent.iterdir()) == {TargetPath}
    assert OutputValue.getvalue() == b"" and OutputValue.tell() == 0


# the writer bridge uses measured and independent neutral profiles with their real readback and publication outcomes
def TestPartWriter() -> None:
    Cases = (
        ("sdk public skew", ((-14.0, -3.0), (23.0, 1.0), (4.0, 25.0)), False),
        (
            "sdk 公開 step",
            (
                (-9.0, -7.0),
                (22.0, -7.0),
                (22.0, 14.0),
                (3.0, 14.0),
                (3.0, 5.0),
                (-9.0, 5.0),
            ),
            True,
        ),
    )
    for RoleName, LineCount in (("Skew", 3), ("Step", 6)):
        with TempDirectory() as FolderName:
            VerifyMeasured(FilePath(FolderName), RoleName, LineCount)
    for NameValue, Corners, IsStepped in Cases:
        Request = MakePolygonCase(NameValue, Corners, IsStepped)
        Document = CastValue(CadDocument, FromData(Request["document"]))
        with TempDirectory() as FolderName:
            TargetPath = FilePath(FolderName) / (NameValue + ".SLDPRT")
            VerifyUntested(Document, TargetPath, len(Corners))
