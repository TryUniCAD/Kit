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
from convert.adapters.solidworks.programs.resolved.polyline.fivepoint.Program import (
    EncodeProgram,
    PadFieldMap,
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
KResolvedDigest = "58f24db25ce3a7069b511e2b551ead8228234971932fc95a28a7d5e264020bab"


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


def TestFCPTP() -> None:
    Overrides = PadFieldMap(KPoints, 9.0)
    PayloadData = EncodeProgram(Overrides)
    assert len(PayloadData) == 11205
    assert Hashlib.sha256(PayloadData).hexdigest() == KResolvedDigest
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
    assert CursorPos == len(PayloadData)
    assert ObjectCount == 332
    assert DefineCount == 40
    assert Overrides[6121] == 0.0
    assert Overrides[6623] == 0.019
    assert (
        Overrides[10014]
        == Overrides[10086]
        == Overrides[10574]
        == Overrides[10598]
        == 0.009
    )


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
        WriteDoc(SourceDoc, TmpPath / "Open.SLDPRT", allow_carrier=False)


def TestCrossFails(TmpPath: FilePath) -> None:
    Crossed = (KPoints[0], KPoints[1], KPoints[4], KPoints[2], KPoints[3])
    SourceDoc = BuildDocument(Crossed)
    assert HasVendorPartEncoding(SourceDoc) is False
    with PytestLib.raises(ApplicationUsabilityError):
        WriteDoc(SourceDoc, TmpPath / "Crossing.SLDPRT", allow_carrier=False)
