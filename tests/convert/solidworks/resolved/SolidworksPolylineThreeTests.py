from __future__ import annotations

from dataclasses import replace as ReplaceData
from pathlib import Path as FilePath

import pytest as PytestLib

from convert import write_document as WriteDoc
from convert.adapters.base import ReadOptions
from convert.adapters.base.UsabilityError import ApplicationUsabilityError
from convert.adapters.solidworks import SldprtArchive
from convert.adapters.solidworks.container.Format import (
    CONFIGURATION_STREAM as ConfigStream,
    KEYWORDS_STREAM as KeyStream,
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
from interchange.geometry.models.Sketch import SketchRelation
from tests.convert.solidworks.resolved.SolidworksPolylineFiveTests import BuildDocument

KPoints = ((0.0, 0.0), (42.0, 0.0), (12.0, 31.0))


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
    RequireTriFrame(ArchiveData, TargetPath)


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
    with PytestLib.raises(ApplicationUsabilityError):
        _ = WriteDoc(SourceDoc, TmpPath / "Relations.SLDPRT", allow_carrier=False)
