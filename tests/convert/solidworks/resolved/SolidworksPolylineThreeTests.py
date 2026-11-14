from __future__ import annotations

from dataclasses import replace as ReplaceData
from pathlib import Path as FilePath
import struct as StructLib
from typing import cast as CastValue
import xml.etree.ElementTree as XmlTree

import pytest as PytestLib

from convert import open_document as OpenDoc
from convert import write_document as WriteDoc
from convert.adapters.base import ParseUntrusted, ReadOptions
from convert.adapters.solidworks import SldprtArchive
from convert.adapters.solidworks.container.Container import (
    BuildSldprt,
    SldprtFormatError,
)
from convert.adapters.solidworks.container.Format import (
    CONFIGURATION_STREAM as ConfigStream,
    KEYWORDS_STREAM as KeyStream,
    KIT_DOCUMENT_STREAM as KitDocStream,
    KIT_NATIVE_STREAM as KitNativeStream,
    RESOLVED_FEATURES_STREAM as ResolvedStream,
)
from convert.adapters.solidworks.core.Adapter import ReadNativePart, SldprtAdapter
from convert.adapters.solidworks.core.Native import (
    HasVendorPartEncoding,
    decode_native_model as DecodeNativeModel,
)
from convert.adapters.solidworks.programs.resolved.polyline.threepoint.Registry import (
    KFieldOwners,
    KResolvedOps,
)
from interchange import Vector3 as VectorThree
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumValues import ParameterRole, ValueKind
from interchange.features.FeatureExtrude import ExtrudeFeature
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Sketch import SketchRelation
from interchange.records.RecordConfig import Configuration
from interchange.records.RecordParameter import Parameter, ParameterValue
from tests.convert.solidworks.resolved.SolidworksPolylineFiveTests import BuildDocument

KPoints = ((0.0, 0.0), (42.0, 0.0), (12.0, 31.0))
KPointOffsets = (6121, 6129, 6299, 6307, 6461, 6469)
KPrecisionPoints = (
    (-7.123456789012345, -11.234567890123456),
    (39.34567890123456, -4.456789012345678),
    (17.567890123456787, 38.67890123456789),
)


def BuildVariant(TargetPath: FilePath, Changes: dict[str, bytes]) -> bytes:
    Template = TargetPath.read_bytes()
    ArchiveData = SldprtArchive.open(TargetPath)
    Streams = {
        NameValue: Payload
        for NameValue, Payload in ArchiveData.streams.items()
        if NameValue not in {KitDocStream, KitNativeStream}
    }
    return BuildSldprt(
        {**Streams, **Changes},
        Template=Template,
        FormatVersion=ArchiveData.format_version,
    )


def EncodeLabels(Keywords: bytes) -> bytes:
    Start = Keywords.find(b"<")
    RootElement = ParseUntrusted(Keywords[Start:])
    Found = 0
    for Element in RootElement.iter():
        if (
            Element.tag.rsplit("}", 1)[-1] == "Dimension"
            and Element.attrib.get("Name") == "D1"
        ):
            setattr(Element, "text", "18.00")
            Found += 1
    assert Found > 0
    Encoded = CastValue(
        bytes, XmlTree.tostring(RootElement, encoding="utf-8", xml_declaration=True)
    )
    return Keywords[:Start] + Encoded


def RequireTriFrame(ArchiveData: SldprtArchive, TargetPath: FilePath) -> None:
    OutputData = ArchiveData.require(ResolvedStream)
    CursorPos = 0
    ObjectCount = 0
    DefineCount = 0
    for StartPos, FieldWidth, OwnerIndex, KindName, _ in KResolvedOps:
        assert StartPos == CursorPos
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(KFieldOwners)
        ObjectCount += KindName in {"definition", "classref", "objectref", "null"}
        DefineCount += KindName == "definition"
        CursorPos += FieldWidth
    assert CursorPos == len(OutputData) == 10601
    assert len(KResolvedOps) == 2518
    assert len(KFieldOwners) == 495
    assert ObjectCount == 300
    assert DefineCount == 40
    Document = ReadNativePart(
        SldprtAdapter(),
        ArchiveData,
        TargetPath.read_bytes(),
        str(TargetPath),
        ReadOptions(include_brep=False),
    )
    assert len(Document.sketches) == 1
    assert len(Document.sketches[0].entities) == 3
    assert len(Document.sketches[0].closed_profile_entity_ids) == 1
    assert len(Document.sketches[0].closed_profile_entity_ids[0]) == 3
    assert "_MO_VERSION_19000/Biography" in ArchiveData.streams
    assert len(ArchiveData.require("Contents/Definition")) == 3816
    assert len(ArchiveData.require("Contents/CMgr")) == 2159
    assert len(ArchiveData.require(ConfigStream)) == 25476


def TestThreeWrite(TmpPath: FilePath) -> None:
    TargetPath = TmpPath / "NativeTriangle.SLDPRT"
    SourceDoc = BuildDocument(KPoints, Depth=9.0)
    Result = WriteDoc(SourceDoc, TargetPath, allow_carrier=False)
    ArchiveData = SldprtArchive.open(TargetPath)
    NativeData = DecodeNativeModel(
        ArchiveData.require(KeyStream),
        ArchiveData.require(ResolvedStream),
        ArchiveData.require(ConfigStream),
        resolved_stream=ResolvedStream,
    )
    assert HasVendorPartEncoding(SourceDoc) is True
    assert Result.IsVendorLoadable is True
    assert Result.IsAppUsable is True
    assert Result.IsNearLossless is True
    assert NativeData.operations[0].object_id == 32
    assert NativeData.operations[0].profile_id == 26
    assert NativeData.operations[0].direction_code == 0
    assert NativeData.operations[0].termination_code == 0
    assert NativeData.operations[0].length_mm == PytestLib.approx(9.0)
    assert NativeData.bounding_box is not None
    assert NativeData.bounding_box.center_mm == PytestLib.approx((21.0, 15.5, 4.5))
    assert NativeData.sketches[0].profiles[0].kind == "polyline"
    assert len(NativeData.sketches[0].profiles[0].coordinates) == 6
    assert NativeData.bounding_box.diameter_mm == PytestLib.approx(52.97169055259611)
    RequireTriFrame(ArchiveData, TargetPath)


def TestTriRewrite(TmpPath: FilePath) -> None:
    FirstPath = TmpPath / "RoundTrip.SLDPRT"
    SecondPath = TmpPath / "RoundTripAgain.SLDPRT"
    _ = WriteDoc(BuildDocument(KPoints, Depth=13.0), FirstPath, allow_carrier=False)
    ArchiveData = SldprtArchive.open(FirstPath)
    Reopened = ReadNativePart(
        SldprtAdapter(),
        ArchiveData,
        FirstPath.read_bytes(),
        str(FirstPath),
        ReadOptions(include_brep=False),
    )
    Definition = Reopened.feature_timeline[-1].definition
    assert isinstance(Definition, ExtrudeFeature)
    assert Definition.offset is None
    assert Definition.draft_angle is None
    assert HasVendorPartEncoding(Reopened) is True
    _ = WriteDoc(Reopened, SecondPath)
    Rewritten = SldprtArchive.open(SecondPath)
    assert "_MO_VERSION_19000/Biography" in Rewritten.streams
    NativeData = DecodeNativeModel(
        Rewritten.require(KeyStream),
        Rewritten.require(ResolvedStream),
        Rewritten.require(ConfigStream),
        resolved_stream=ResolvedStream,
    )
    assert NativeData.operations[0].object_id == 32
    assert NativeData.operations[0].profile_id == 26
    assert NativeData.operations[0].length_mm == PytestLib.approx(13.0)
    assert len(NativeData.sketches[0].profiles[0].coordinates) == 6


def TestTriPrecise(TmpPath: FilePath) -> None:
    Points = ((0.1, 0.2), (42.0, 0.3), (12.0, 31.0))
    FirstPath = TmpPath / "PreciseRoundTrip.SLDPRT"
    SecondPath = TmpPath / "PreciseRoundTripAgain.SLDPRT"
    _ = WriteDoc(BuildDocument(Points, Depth=13.0), FirstPath, allow_carrier=False)
    ArchiveData = SldprtArchive.open(FirstPath)
    Reopened = ReadNativePart(
        SldprtAdapter(),
        ArchiveData,
        FirstPath.read_bytes(),
        str(FirstPath),
        ReadOptions(include_brep=False),
    )
    _ = WriteDoc(Reopened, SecondPath)
    FirstResolved = ArchiveData.require(ResolvedStream)
    SecondResolved = SldprtArchive.open(SecondPath).require(ResolvedStream)
    for OffsetPos in KPointOffsets:
        assert (
            FirstResolved[OffsetPos : OffsetPos + 8]
            == SecondResolved[OffsetPos : OffsetPos + 8]
        )


def TestDirection(TmpPath: FilePath) -> None:
    SourceDoc = BuildDocument(KPoints)
    for Index, Direction in enumerate(
        (VectorThree(0.0, 0.0, 2.0), VectorThree(5e-13, 0.0, 1.0))
    ):
        FeatureData = SourceDoc.feature_timeline[0]
        assert isinstance(FeatureData.definition, ExtrudeFeature)
        FeatureData = ReplaceData(
            FeatureData,
            definition=ReplaceData(FeatureData.definition, direction=Direction),
        )
        Changed = ReplaceData(SourceDoc, feature_timeline=(FeatureData,))
        assert HasVendorPartEncoding(Changed) is False
        with PytestLib.raises(SldprtFormatError):
            _ = WriteDoc(Changed, TmpPath / f"DirectionLoss{Index}.SLDPRT")


def TestPadAlias(TmpPath: FilePath) -> None:
    SourceDoc = BuildDocument(KPoints)
    Changed = ReplaceData(
        SourceDoc,
        parameters=tuple(
            (
                ReplaceData(
                    ParamData,
                    value=ParameterValue(5e-11, ValueKind.LENGTH, "mm"),
                    attributes={"freecad_path": "Offset"},
                )
                if ParamData.attributes.get("freecad_path") == "Length"
                else ParamData
            )
            for ParamData in SourceDoc.parameters
        ),
    )
    assert HasVendorPartEncoding(Changed) is False
    with PytestLib.raises(SldprtFormatError):
        _ = WriteDoc(Changed, TmpPath / "PadAliasLoss.SLDPRT")


def TestPadValue(TmpPath: FilePath) -> None:
    SourceDoc = BuildDocument(KPoints)
    Changed = ReplaceData(
        SourceDoc,
        parameters=tuple(
            (
                ReplaceData(
                    ParamData,
                    value=ParameterValue(0.0, ValueKind.NUMBER, ""),
                )
                if ParamData.attributes.get("freecad_path") == "FuzzyTolerance"
                else ParamData
            )
            for ParamData in SourceDoc.parameters
        ),
    )
    assert HasVendorPartEncoding(Changed) is False
    with PytestLib.raises(SldprtFormatError):
        _ = WriteDoc(Changed, TmpPath / "PadValueLoss.SLDPRT")


def TestFivePrecise(TmpPath: FilePath) -> None:
    Points = (
        (0.1234567890123, 0.0),
        (35.0, 0.0),
        (42.0, 17.0),
        (19.0, 32.0),
        (-5.0, 14.0),
    )
    FirstPath = TmpPath / "FivePrecise.SLDPRT"
    SecondPath = TmpPath / "FivePreciseAgain.SLDPRT"
    _ = WriteDoc(BuildDocument(Points, Depth=9.0), FirstPath, allow_carrier=False)
    FirstArchive = SldprtArchive.open(FirstPath)
    FirstRead = ReadNativePart(
        SldprtAdapter(),
        FirstArchive,
        FirstPath.read_bytes(),
        str(FirstPath),
        ReadOptions(include_brep=False),
    )
    _ = WriteDoc(FirstRead, SecondPath)
    SecondArchive = SldprtArchive.open(SecondPath)
    SecondRead = ReadNativePart(
        SldprtAdapter(),
        SecondArchive,
        SecondPath.read_bytes(),
        str(SecondPath),
        ReadOptions(include_brep=False),
    )
    FirstEdges = tuple(
        (
            Geometry.start.x,
            Geometry.start.y,
            Geometry.end.x,
            Geometry.end.y,
        )
        for Geometry in (Entity.geometry for Entity in FirstRead.sketches[0].entities)
        if isinstance(Geometry, LineGeometry)
    )
    SecondEdges = tuple(
        (
            Geometry.start.x,
            Geometry.start.y,
            Geometry.end.x,
            Geometry.end.y,
        )
        for Geometry in (Entity.geometry for Entity in SecondRead.sketches[0].entities)
        if isinstance(Geometry, LineGeometry)
    )
    assert len(FirstEdges) == 5
    assert FirstEdges == SecondEdges


def TestTriExtra(TmpPath: FilePath) -> None:
    SourceDoc = BuildDocument(KPoints)
    SecondSketch = ReplaceData(SourceDoc.sketches[0], id="test:sketch:second")
    Changed = ReplaceData(SourceDoc, sketches=(*SourceDoc.sketches, SecondSketch))
    assert HasVendorPartEncoding(Changed) is False
    with PytestLib.raises(SldprtFormatError):
        _ = WriteDoc(Changed, TmpPath / "TriExtra.SLDPRT")


def TestThreeDepth(TmpPath: FilePath) -> None:
    Points = ((-7.0, -11.0), (39.0, -4.0), (17.0, 38.0))
    SourceDoc = BuildDocument(Points, Depth=17.0)
    TargetPath = TmpPath / "ShiftedTriangle.SLDPRT"
    Result = WriteDoc(SourceDoc, TargetPath, allow_carrier=False)
    ArchiveData = SldprtArchive.open(TargetPath)
    NativeData = DecodeNativeModel(
        ArchiveData.require(KeyStream),
        ArchiveData.require(ResolvedStream),
        ArchiveData.require(ConfigStream),
        resolved_stream=ResolvedStream,
    )
    assert Result.IsVendorLoadable is True
    assert Result.IsAppUsable is True
    assert Result.IsNearLossless is True
    assert NativeData.operations[0].length_mm == PytestLib.approx(17.0)
    assert NativeData.bounding_box is not None
    assert NativeData.bounding_box.center_mm == PytestLib.approx((16.0, 13.5, 8.5))
    ExpectedDiameter = 2.0 * ((23.0**2 + 24.5**2 + 8.5**2) ** 0.5)
    assert NativeData.bounding_box.diameter_mm == PytestLib.approx(ExpectedDiameter)
    ResolvedData = ArchiveData.require(ResolvedStream)
    for OffsetPos in (8225, 8447):
        DiameterMetres = StructLib.unpack_from("<d", ResolvedData, OffsetPos)[0]
        assert DiameterMetres * 1000.0 == PytestLib.approx(ExpectedDiameter)
    RequireTriFrame(ArchiveData, TargetPath)


def TestPrecision(TmpPath: FilePath) -> None:
    Points = KPrecisionPoints
    SourceDoc = BuildDocument(Points, Depth=13.375)
    TargetPath = TmpPath / "PreciseTriangle.SLDPRT"
    Result = WriteDoc(SourceDoc, TargetPath, allow_carrier=False)
    assert HasVendorPartEncoding(SourceDoc) is True
    assert Result.IsVendorLoadable is True
    assert Result.IsAppUsable is True
    assert Result.IsNearLossless is True
    ResolvedData = SldprtArchive.open(TargetPath).require(ResolvedStream)
    ExpectedMetres = tuple(
        Coordinate / 1000.0 for Point in Points for Coordinate in Point
    )
    for OffsetPos, Expected in zip(KPointOffsets, ExpectedMetres, strict=True):
        assert ResolvedData[OffsetPos : OffsetPos + 8] == StructLib.pack("<d", Expected)
    RequireTriFrame(SldprtArchive.open(TargetPath), TargetPath)


def TestNearOrigin(TmpPath: FilePath) -> None:
    Points = ((8e-13, 0.0), (42.0, 0.0), (12.0, 31.0))
    TargetPath = TmpPath / "NearOriginTriangle.SLDPRT"
    Result = WriteDoc(BuildDocument(Points), TargetPath, allow_carrier=False)
    assert Result.IsVendorLoadable is True
    assert Result.IsAppUsable is True
    assert Result.IsNearLossless is True
    ArchiveData = SldprtArchive.open(TargetPath)
    ResolvedData = ArchiveData.require(ResolvedStream)
    assert ResolvedData[6121:6129] == StructLib.pack("<d", 8e-13 / 1000.0)
    RequireTriFrame(ArchiveData, TargetPath)


def RequireTriRead(Document: CadDocument, Baseline: bytes) -> None:
    ExpectedDepth = StructLib.unpack_from("<d", Baseline, 9408)[0] * 1000.0
    DepthParam = next(Param for Param in Document.parameters if Param.name == "D1")
    assert DepthParam.value.value == ExpectedDepth
    for Index, Entity in enumerate(Document.sketches[0].entities):
        assert isinstance(Entity.geometry, LineGeometry)
        for Point, Offset in (
            (Entity.geometry.start, KPointOffsets[Index * 2]),
            (Entity.geometry.end, KPointOffsets[((Index + 1) % 3) * 2]),
        ):
            Expected = StructLib.unpack_from("<d", Baseline, Offset)[0] * 1000.0
            ExpectedNext = StructLib.unpack_from("<d", Baseline, Offset + 8)[0] * 1000.0
            assert (Point.x, Point.y) == (Expected, ExpectedNext)


def TestLabels(TmpPath: FilePath) -> None:
    SourcePath = TmpPath / "NativeSource.SLDPRT"
    _ = WriteDoc(
        BuildDocument(KPrecisionPoints, Depth=17.995855),
        SourcePath,
        allow_carrier=False,
    )
    ArchiveData = SldprtArchive.open(SourcePath)
    Baseline = ArchiveData.require(ResolvedStream)
    Labels = EncodeLabels(ArchiveData.require(KeyStream))
    _ = SourcePath.write_bytes(BuildVariant(SourcePath, {KeyStream: Labels}))
    Document = OpenDoc(SourcePath, include_brep=False)
    RequireTriRead(Document, Baseline)


def TestDepthGuard(TmpPath: FilePath) -> None:
    SourcePath = TmpPath / "InvalidTriangleDepth.SLDPRT"
    _ = WriteDoc(BuildDocument(KPoints), SourcePath, allow_carrier=False)
    ArchiveData = SldprtArchive.open(SourcePath)
    Payload = bytearray(ArchiveData.require(ResolvedStream))
    StructLib.pack_into("<d", Payload, 9408, 0.03125)
    _ = SourcePath.write_bytes(
        BuildVariant(SourcePath, {ResolvedStream: bytes(Payload)})
    )
    with PytestLib.raises(SldprtFormatError):
        _ = OpenDoc(SourcePath)


def TestParamLoss(TmpPath: FilePath) -> None:
    SourceDoc = BuildDocument(KPoints)
    FeatureId = SourceDoc.feature_timeline[0].id
    Cases = (
        (SourceDoc.sketches[0].id, "Count", 2, ValueKind.NUMBER, "", "CustomCount"),
        (FeatureId, "Count", 2, ValueKind.NUMBER, "", "CustomCount"),
        (FeatureId, "CustomLength", 3.5, ValueKind.LENGTH, "mm", "CustomLength"),
    )
    for Index, (
        OwnerId,
        NameValue,
        Scalar,
        KindValue,
        UnitValue,
        PathValue,
    ) in enumerate(Cases):
        ExtraParam = Parameter(
            f"test:parameter:{Index}",
            NameValue,
            ParameterValue(Scalar, KindValue, UnitValue),
            owner_id=OwnerId,
            attributes={"freecad_path": PathValue},
        )
        Changed = ReplaceData(SourceDoc, parameters=(*SourceDoc.parameters, ExtraParam))
        assert HasVendorPartEncoding(Changed) is False
        with PytestLib.raises(SldprtFormatError):
            _ = WriteDoc(Changed, TmpPath / f"ParamLoss{Index}.SLDPRT")


def TestFuzzyLoss(TmpPath: FilePath) -> None:
    SourceDoc = BuildDocument(KPoints)
    Changed = ReplaceData(
        SourceDoc,
        parameters=tuple(
            (
                ReplaceData(
                    ParamData,
                    value=ParameterValue(-1.0 + 5e-11, ValueKind.NUMBER, ""),
                )
                if ParamData.attributes.get("freecad_path") == "FuzzyTolerance"
                else ParamData
            )
            for ParamData in SourceDoc.parameters
        ),
    )
    assert HasVendorPartEncoding(Changed) is False
    with PytestLib.raises(SldprtFormatError):
        _ = WriteDoc(Changed, TmpPath / "FuzzyLoss.SLDPRT")


def TestOffsetLoss(TmpPath: FilePath) -> None:
    SourceDoc = BuildDocument(KPoints)
    FeatureData = SourceDoc.feature_timeline[0]
    assert isinstance(FeatureData.definition, ExtrudeFeature)
    FeatureData = ReplaceData(
        FeatureData,
        definition=ReplaceData(
            FeatureData.definition,
            offset=ParameterValue(5e-11, ValueKind.LENGTH, "mm"),
        ),
    )
    Changed = ReplaceData(
        SourceDoc,
        feature_timeline=(FeatureData,),
        parameters=tuple(
            (
                ReplaceData(
                    ParamData,
                    value=ParameterValue(5e-11, ValueKind.LENGTH, "mm"),
                )
                if ParamData.attributes.get("freecad_path") == "Offset"
                else ParamData
            )
            for ParamData in SourceDoc.parameters
        ),
    )
    assert HasVendorPartEncoding(Changed) is False
    with PytestLib.raises(SldprtFormatError):
        _ = WriteDoc(Changed, TmpPath / "OffsetLoss.SLDPRT")


def TestStaleDepth(TmpPath: FilePath) -> None:
    SourceDoc = BuildDocument(KPoints)
    Changed = ReplaceData(
        SourceDoc,
        parameters=tuple(
            (
                ReplaceData(
                    ParamData,
                    value=ParameterValue(4.0, ValueKind.LENGTH, "mm"),
                )
                if ParamData.attributes.get("freecad_path") == "Length"
                else ParamData
            )
            for ParamData in SourceDoc.parameters
        ),
    )
    assert HasVendorPartEncoding(Changed) is False
    with PytestLib.raises(SldprtFormatError):
        _ = WriteDoc(Changed, TmpPath / "StaleDepth.SLDPRT")


def TestUnitLoss(TmpPath: FilePath) -> None:
    SourceDoc = BuildDocument(KPoints)
    Changed = ReplaceData(
        SourceDoc,
        parameters=tuple(
            (
                ReplaceData(
                    ParamData,
                    value=ParameterValue(0.9, ValueKind.LENGTH, "ft"),
                )
                if ParamData.attributes.get("freecad_path") == "Length"
                else ParamData
            )
            for ParamData in SourceDoc.parameters
        ),
    )
    assert HasVendorPartEncoding(Changed) is False
    with PytestLib.raises(SldprtFormatError):
        _ = WriteDoc(Changed, TmpPath / "UnitLoss.SLDPRT")


def TestDepthUnit(TmpPath: FilePath) -> None:
    SourceDoc = BuildDocument(KPoints)
    FeatureData = SourceDoc.feature_timeline[0]
    assert isinstance(FeatureData.definition, ExtrudeFeature)
    FeatureData = ReplaceData(
        FeatureData,
        definition=ReplaceData(
            FeatureData.definition,
            length=ParameterValue(9.0, ValueKind.LENGTH, "cm"),
        ),
    )
    Changed = ReplaceData(SourceDoc, feature_timeline=(FeatureData,))
    assert HasVendorPartEncoding(Changed) is False
    with PytestLib.raises(SldprtFormatError):
        _ = WriteDoc(Changed, TmpPath / "DepthUnitLoss.SLDPRT")


def TestPadPathLoss(TmpPath: FilePath) -> None:
    SourceDoc = BuildDocument(KPoints)
    ExtraParam = Parameter(
        "test:parameter:tolerance",
        "CustomTolerance",
        ParameterValue(-1.0, ValueKind.NUMBER, ""),
        owner_id=SourceDoc.feature_timeline[0].id,
        attributes={"freecad_path": "FuzzyTolerance"},
    )
    Changed = ReplaceData(SourceDoc, parameters=(*SourceDoc.parameters, ExtraParam))
    assert HasVendorPartEncoding(Changed) is False
    with PytestLib.raises(SldprtFormatError):
        _ = WriteDoc(Changed, TmpPath / "PadPathLoss.SLDPRT")


def TestRoleLoss(TmpPath: FilePath) -> None:
    SourceDoc = BuildDocument(KPoints)
    Changed = ReplaceData(
        SourceDoc,
        parameters=tuple(
            (
                ReplaceData(ParamData, role=ParameterRole.DRIVEN)
                if ParamData.attributes.get("freecad_path") == "Length"
                else ParamData
            )
            for ParamData in SourceDoc.parameters
        ),
    )
    assert HasVendorPartEncoding(Changed) is False
    with PytestLib.raises(SldprtFormatError):
        _ = WriteDoc(Changed, TmpPath / "RoleLoss.SLDPRT")


def TestConfigLoss(TmpPath: FilePath) -> None:
    SourceDoc = BuildDocument(KPoints)
    SecondConfig = Configuration("second", "Second")
    Changed = ReplaceData(
        SourceDoc,
        configurations=(*SourceDoc.configurations, SecondConfig),
    )
    assert HasVendorPartEncoding(Changed) is False
    with PytestLib.raises(SldprtFormatError):
        _ = WriteDoc(Changed, TmpPath / "ConfigLoss.SLDPRT")


def TestLabelLoss(TmpPath: FilePath) -> None:
    SourceDoc = BuildDocument(KPoints)
    Changed = ReplaceData(
        SourceDoc,
        parameters=tuple(
            (
                ReplaceData(
                    ParamData,
                    value=ParameterValue("Custom", ValueKind.STRING, ""),
                )
                if ParamData.attributes.get("freecad_path") == "Label2"
                else ParamData
            )
            for ParamData in SourceDoc.parameters
        ),
    )
    assert HasVendorPartEncoding(Changed) is False
    with PytestLib.raises(SldprtFormatError):
        _ = WriteDoc(Changed, TmpPath / "LabelLoss.SLDPRT")


def TestOpenWire(TmpPath: FilePath) -> None:
    SourceDoc = BuildDocument(KPoints)
    First = SourceDoc.sketches[0].entities[0]
    assert isinstance(First.geometry, LineGeometry)
    EndPoint = ReplaceData(First.geometry.end, x=First.geometry.end.x + 1.0)
    Geometry = ReplaceData(First.geometry, end=EndPoint)
    Entities = (
        ReplaceData(First, geometry=Geometry),
        *SourceDoc.sketches[0].entities[1:],
    )
    Sketch = ReplaceData(SourceDoc.sketches[0], entities=Entities)
    SourceDoc = ReplaceData(SourceDoc, sketches=(Sketch,))
    assert HasVendorPartEncoding(SourceDoc) is False
    with PytestLib.raises(SldprtFormatError):
        _ = WriteDoc(SourceDoc, TmpPath / "OpenWire.SLDPRT")


def TestThreeTie(TmpPath: FilePath) -> None:
    Points = ((0.0, 0.0), (36.0, 0.0), (36.0, 24.0))
    TargetPath = TmpPath / "TriangleAttachments.SLDPRT"
    Result = WriteDoc(
        BuildDocument(Points, Depth=11.0), TargetPath, allow_carrier=False
    )
    assert Result.IsVendorLoadable is True
    assert Result.IsAppUsable is True
    assert Result.IsNearLossless is True
    ArchiveData = SldprtArchive.open(TargetPath)
    NativeData = DecodeNativeModel(
        ArchiveData.require(KeyStream),
        ArchiveData.require(ResolvedStream),
        ArchiveData.require(ConfigStream),
        resolved_stream=ResolvedStream,
    )
    assert NativeData.operations[0].length_mm == PytestLib.approx(11.0)
    RequireTriFrame(ArchiveData, TargetPath)


def TestRelations(TmpPath: FilePath) -> None:
    SourceDoc = BuildDocument(KPoints)
    Sketch = ReplaceData(
        SourceDoc.sketches[0],
        constraints=(SketchRelation("relation:0", "horizontal", ()),),
    )
    SourceDoc = ReplaceData(SourceDoc, sketches=(Sketch,))
    assert HasVendorPartEncoding(SourceDoc) is False
    with PytestLib.raises(SldprtFormatError):
        _ = WriteDoc(SourceDoc, TmpPath / "Relations.SLDPRT")
