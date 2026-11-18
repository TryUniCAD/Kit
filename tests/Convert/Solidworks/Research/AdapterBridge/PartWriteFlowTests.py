from dataclasses import replace as ReplaceValue
from io import BytesIO
from math import isclose as IsClose
from pathlib import Path as FilePath
from tempfile import TemporaryDirectory as TempDirectory
from typing import cast as CastValue

from convert import open_document as OpenDoc, write_document as WriteDoc
from convert.adapters.registry.RegistryErrors import NotFoundError
from interchange.document.Models.DocumentModel import CadDocument
from interchange.serialization.Deserialize import FromData
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


# the registered writer must exercise actual transactional paths and caller owned streams with two independent neutral designs
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
    with TempDirectory() as RootValue:
        for IndexValue, (NameValue, VerticesValue, VariantValue) in enumerate(Cases):
            RequestValue = MakePolygonCase(NameValue, VerticesValue, VariantValue)
            DocumentValue = CastValue(CadDocument, FromData(RequestValue["document"]))
            TargetPath = FilePath(RootValue) / str(IndexValue) / (NameValue + ".SLDPRT")
            StrictValues = {"require_native_transfers": True}
            PathResult = WriteDoc(
                DocumentValue, TargetPath, allow_carrier=False, values=StrictValues
            )
            assert PathResult.path == TargetPath.resolve()
            assert PathResult.bytes_written == TargetPath.stat().st_size
            assert PathResult.application_usable and PathResult.vendor_loadable
            assert len(PathResult.native_capabilities) == 6
            StreamValue = BytesIO()
            StreamResult = WriteDoc(
                DocumentValue,
                StreamValue,
                destination_format="SOLIDWORKS.SLDPRT",
                allow_carrier=False,
                values={**StrictValues, "final_destination": str(TargetPath)},
            )
            assert StreamResult.path is None
            assert StreamResult.bytes_written == len(StreamValue.getvalue())
            assert StreamResult.native_capabilities == PathResult.native_capabilities
            DepthValue = CastValue(float, DocumentValue.parameters[0].value.value)
            VerifyPart(TargetPath, len(VerticesValue), DepthValue)
            VerifyPart(StreamValue.getvalue(), len(VerticesValue), DepthValue)
            VerifyRejects(DocumentValue, TargetPath)
