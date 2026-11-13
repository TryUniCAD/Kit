from __future__ import annotations
import hashlib as Hashlib
from dataclasses import replace as ReplaceData
from pathlib import Path as FilePath

import pytest as PytestLib

from convert import open_document as OpenDoc
from convert import write_document as WriteDoc
from convert.adapters.base.UsabilityError import ApplicationUsabilityError
from convert.adapters.solidworks import SldprtArchive
from convert.adapters.solidworks.container.Format import (
    CONFIGURATION_STREAM as ConfigStream,
    KEYWORDS_STREAM as KeyStream,
    RESOLVED_FEATURES_STREAM as ResolvedStream,
)
from convert.adapters.solidworks.core.Native import (
    HasVendorPartEncoding,
    decode_native_model as DecodeNativeModel,
)
from convert.adapters.solidworks.programs.resolved.polyline.fivepoint.Registry import (
    KFieldOwners,
    KResolvedOps,
)
from tests.convert.solidworks.core.SolidworksWriterTests import FreecadRPD
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumGeometry import GeometryKind
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Sketch import SketchEntity
from interchange.geometry.models.VectorPlane import PlaneVector

KPoints = (
    (0.0, 0.0),
    (35.0, 0.0),
    (42.0, 17.0),
    (19.0, 32.0),
    (-5.0, 14.0),
)
KResolvedDigest = "cbd02ec7dc243cffe942106d788ff33193efebbe9beae49a2e498c660a66902d"


def BuildDocument(
    Points: tuple[tuple[float, float], ...] = KPoints, Depth: float = 9.0
) -> CadDocument:
    SourceDoc = FreecadRPD(Depth=Depth)
    Entities = tuple(
        SketchEntity(
            f"edge:{Index}",
            GeometryKind.LINE,
            LineGeometry(
                PlaneVector(*Points[Index]),
                PlaneVector(*Points[(Index + 1) % len(Points)]),
            ),
        )
        for Index in range(len(Points))
    )
    Sketch = ReplaceData(
        SourceDoc.sketches[0],
        entities=Entities,
        closed_profile_entity_ids=(tuple(Entity.id for Entity in Entities),),
        constraints=(),
        parameter_ids=(),
    )
    return ReplaceData(SourceDoc, sketches=(Sketch,))


def RequireFCFrame(ResolvedData: bytes) -> None:
    assert len(KResolvedOps) == 2708
    assert len(KFieldOwners) == 495
    CursorPos = 0
    ObjectCount = 0
    DefineCount = 0
    for StartPos, FieldWidth, OwnerIndex, KindName, _ in KResolvedOps:
        assert StartPos == CursorPos
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(KFieldOwners)
        assert KindName in {
            "definition",
            "classref",
            "objectref",
            "null",
            "string",
        } or KindName.startswith(("primitive:", "direct:"))
        ObjectCount += KindName in {"definition", "classref", "objectref", "null"}
        DefineCount += KindName == "definition"
        CursorPos += FieldWidth
    assert CursorPos == len(ResolvedData)
    assert ObjectCount == 332
    assert DefineCount == 40


def RequireNVFrame(ArchiveData: SldprtArchive) -> None:
    assert "_MO_VERSION_19000/Biography" in ArchiveData.streams
    assert "_MO_VERSION_18000/Biography" not in ArchiveData.streams
    assert len(ArchiveData.require("Contents/Definition")) == 3816
    assert len(ArchiveData.require("Contents/CMgr")) == 2159
    assert len(ArchiveData.require(ConfigStream)) == 25476


def TestFiveWrite(TmpPath: FilePath) -> None:
    SourceDoc = BuildDocument()
    TargetPath = TmpPath / "PolylineFive.SLDPRT"
    ResultData = WriteDoc(SourceDoc, TargetPath, allow_carrier=False)
    ArchiveData = SldprtArchive.open(TargetPath)
    ResolvedData = ArchiveData.require(ResolvedStream)
    NativeData = DecodeNativeModel(
        ArchiveData.require(KeyStream),
        ResolvedData,
        ArchiveData.require(ConfigStream),
        resolved_stream=ResolvedStream,
    )
    assert HasVendorPartEncoding(SourceDoc)
    assert ResultData.IsVendorLoadable is True
    assert ResultData.IsAppUsable is True
    assert ResultData.IsNearLossless is True
    assert len(ResolvedData) == 11205
    assert Hashlib.sha256(ResolvedData).hexdigest() == KResolvedDigest
    RequireFCFrame(ResolvedData)
    assert NativeData.bounding_box is not None
    assert NativeData.bounding_box.center_mm == PytestLib.approx((18.5, 16.0, 4.5))
    assert NativeData.bounding_box.diameter_mm == PytestLib.approx(57.56735185849701)
    RequireNVFrame(ArchiveData)
    assert tuple(
        (Evalue.kind, Evalue.coordinates) for Evalue in NativeData.sketches[0].profiles
    ) == (("polyline", (0.0, 0.0, 35.0, 0.0, 42.0, 17.0, 19.0, 32.0, -5.0, 14.0)),)
    assert len(NativeData.operations) == 1
    assert NativeData.operations[0].object_id == 32
    assert NativeData.operations[0].profile_id == 26
    assert NativeData.operations[0].direction_code == 0
    assert NativeData.operations[0].termination_code == 0
    assert NativeData.operations[0].length_mm == PytestLib.approx(9.0)
    Reopened = OpenDoc(TargetPath)
    assert len(Reopened.sketches[0].entities) == 5
    assert (
        Reopened.feature_timeline[0].definition
        == SourceDoc.feature_timeline[0].definition
    )


def TestFCPDV(TmpPath: FilePath) -> None:
    Points = (
        (5.0, -10.0),
        (45.0, -5.0),
        (35.0, 25.0),
        (12.0, 37.0),
        (-8.0, 12.0),
    )
    SourceDoc = BuildDocument(Points, Depth=37.0)
    TargetPath = TmpPath / "Shifted37.SLDPRT"
    ResultData = WriteDoc(SourceDoc, TargetPath, allow_carrier=False)
    ArchiveData = SldprtArchive.open(TargetPath)
    NativeData = DecodeNativeModel(
        ArchiveData.require(KeyStream),
        ArchiveData.require(ResolvedStream),
        ArchiveData.require(ConfigStream),
        resolved_stream=ResolvedStream,
    )
    assert ResultData.IsVendorLoadable is True
    assert ResultData.IsAppUsable is True
    assert ResultData.IsNearLossless is True
    assert NativeData.operations[0].length_mm == PytestLib.approx(37.0)
    assert NativeData.bounding_box is not None
    assert NativeData.bounding_box.center_mm == PytestLib.approx((18.5, 13.5, 18.5))
    ExpectedDiameter = 1000.0 * ((26.5**2 + 23.5**2 + 18.5**2) ** 0.5)
    assert NativeData.bounding_box.diameter_mm == PytestLib.approx(ExpectedDiameter)
    RequireNVFrame(ArchiveData)


def TestOpenFails(TmpPath: FilePath) -> None:
    SourceDoc = BuildDocument()
    Sketch = SourceDoc.sketches[0]
    Sketch = ReplaceData(
        Sketch,
        entities=Sketch.entities[:-1],
        closed_profile_entity_ids=(Sketch.closed_profile_entity_ids[0][:-1],),
    )
    SourceDoc = ReplaceData(SourceDoc, sketches=(Sketch,))
    assert HasVendorPartEncoding(SourceDoc) is False
    with PytestLib.raises(ApplicationUsabilityError):
        _ = WriteDoc(SourceDoc, TmpPath / "Open.SLDPRT", allow_carrier=False)


def TestCrossFails(TmpPath: FilePath) -> None:
    Crossed = (KPoints[0], KPoints[1], KPoints[4], KPoints[2], KPoints[3])
    SourceDoc = BuildDocument(Crossed)
    assert HasVendorPartEncoding(SourceDoc) is False
    with PytestLib.raises(ApplicationUsabilityError):
        _ = WriteDoc(SourceDoc, TmpPath / "Crossing.SLDPRT", allow_carrier=False)
