from __future__ import annotations

from dataclasses import replace as ReplaceData
from pathlib import Path as FilePath

import pytest as PytestLib

from convert import ApplicationUsabilityError
from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from convert.adapters.solidworks import SldprtArchive
from convert.adapters.solidworks.container.Format import (
    CONFIGURATION_STREAM as ConfigStream,
    KEYWORDS_STREAM as KeyStream,
    RESOLVED_FEATURES_STREAM as ResolvedStream,
)
from interchange import (
    CylinderSurface,
    ParameterRole,
    PlaneSurface,
    Transform,
    Vector3 as VectorThree,
)
from convert.adapters.solidworks.core.Native import (
    HasVendorPartEncoding,
    decode_native_model as DecodeNativeModel,
)

# tracked v8 directory gives every part a real read and write boundary
KCorpusRoot = (
    FilePath(__file__).resolve().parents[4]
    / "re"
    / "solidworks"
    / "examples"
    / "Single Turbo Dual Overhead Cam V8 - KDP - 2024"
)

# tracked freecad fixtures cover both additive box property schemas
KAddBoxRoot = (
    FilePath(__file__).resolve().parents[4]
    / "re"
    / "solidworks"
    / "examples"
    / "FreeCAD"
)


# corpus gated coverage proves every tracked part round trips natively
@PytestLib.mark.skipif(not KCorpusRoot.is_dir(), reason="v8 part corpus unavailable")
def TestCorpus(TmpPath: FilePath) -> None:
    Parts = tuple(
        sorted(
            (
                PathValue
                for PathValue in KCorpusRoot.iterdir()
                if PathValue.suffix.casefold() == ".sldprt"
            ),
            key=lambda PathValue: PathValue.name,
        )
    )
    assert len(Parts) == 57
    for PartPath in Parts:
        DocumentValue = OpenDocument(PartPath, include_brep=False)
        ResultInfo = WriteDocument(
            DocumentValue, TmpPath / PartPath.name, allow_carrier=False
        )
        assert ResultInfo.metadata["compatibility"] == "native-exact", PartPath.name
        assert ResultInfo.metadata["native_self_contained"] is True, PartPath.name
        assert ResultInfo.application_usable is True, PartPath.name
        assert ResultInfo.near_lossless is True, PartPath.name


# additive box schemas differ across freecad versions so both are accepted
@PytestLib.mark.skipif(not KAddBoxRoot.is_dir(), reason="additive box corpus unavailable")
def TestAddBox(TmpPath: FilePath) -> None:
    SourcePath = KAddBoxRoot / "AdditiveBox-1.1.4.FCStd"
    DocumentValue = OpenDocument(SourcePath)
    assert HasVendorPartEncoding(DocumentValue) is True
    TargetPath = TmpPath / f"{SourcePath.stem}.SLDPRT"
    ResultInfo = WriteDocument(DocumentValue, TargetPath, allow_carrier=False)
    assert ResultInfo.vendor_loadable is True
    assert ResultInfo.application_usable is True
    assert ResultInfo.near_lossless is True
    assert ResultInfo.metadata["native_self_contained"] is True
    ArchiveData = SldprtArchive.open(TargetPath)
    NativeData = DecodeNativeModel(
        ArchiveData.require(KeyStream),
        ArchiveData.require(ResolvedStream),
        ArchiveData.require(ConfigStream),
        resolved_stream=ResolvedStream,
    )
    assert NativeData.sketches[0].profiles[0].kind == "rectangle"
    assert NativeData.sketches[0].profiles[0].coordinates == PytestLib.approx(
        (0.0, 0.0, 20.0, 30.0)
    )
    assert NativeData.operations[0].length_mm == PytestLib.approx(10.0)


# a rotated principal basis must not collapse to canonical axes
@PytestLib.mark.skipif(not KAddBoxRoot.is_dir(), reason="additive box corpus unavailable")
def TestBoxPlane(TmpPath: FilePath) -> None:
    SourcePath = KAddBoxRoot / "AdditiveBox-1.1.4.FCStd"
    DocumentValue = OpenDocument(SourcePath)
    PlaneValue = DocumentValue.support_planes[0]
    Rotated = ReplaceData(
        PlaneValue,
        transform=Transform(
            origin=PlaneValue.transform.origin,
            x_axis=VectorThree(0.0, 1.0, 0.0),
            y_axis=VectorThree(-1.0, 0.0, 0.0),
            z_axis=VectorThree(0.0, 0.0, 1.0),
        ),
    )
    Changed = ReplaceData(
        DocumentValue,
        support_planes=(Rotated, *DocumentValue.support_planes[1:]),
    )
    assert HasVendorPartEncoding(Changed) is False
    with PytestLib.raises(ApplicationUsabilityError):
        _ = WriteDocument(Changed, TmpPath / "RotatedBox.SLDPRT", allow_carrier=False)


# driven dimensions would become driving native dimensions so they decline
@PytestLib.mark.skipif(not KAddBoxRoot.is_dir(), reason="additive box corpus unavailable")
def TestBoxDriven(TmpPath: FilePath) -> None:
    SourcePath = KAddBoxRoot / "AdditiveBox-1.1.4.FCStd"
    DocumentValue = OpenDocument(SourcePath)
    Changed = ReplaceData(
        DocumentValue,
        parameters=tuple(
            (
                ReplaceData(ItemData, role=ParameterRole.DRIVEN)
                if ItemData.attributes.get("freecad_path") == "Length"
                else ItemData
            )
            for ItemData in DocumentValue.parameters
        ),
    )
    assert HasVendorPartEncoding(Changed) is False
    with PytestLib.raises(ApplicationUsabilityError):
        _ = WriteDocument(
            Changed, TmpPath / "DrivenBox.SLDPRT", allow_carrier=False
        )


# curved faces on the box corners would be replaced by flat faces
@PytestLib.mark.skipif(not KAddBoxRoot.is_dir(), reason="additive box corpus unavailable")
def TestBoxCurved(TmpPath: FilePath) -> None:
    SourcePath = KAddBoxRoot / "AdditiveBox-1.1.4.FCStd"
    DocumentValue = OpenDocument(SourcePath)
    BrepValue = DocumentValue.brep
    assert BrepValue is not None
    SurfaceValue = BrepValue.surfaces[0]
    Changed = ReplaceData(
        DocumentValue,
        brep=ReplaceData(
            BrepValue,
            surfaces=(
                CylinderSurface(
                    SurfaceValue.id,
                    VectorThree(0.0, 0.0, 0.0),
                    VectorThree(0.0, 0.0, 1.0),
                    VectorThree(1.0, 0.0, 0.0),
                    5.0,
                ),
                *BrepValue.surfaces[1:],
            ),
        ),
    )
    assert HasVendorPartEncoding(Changed) is False
    with PytestLib.raises(ApplicationUsabilityError):
        _ = WriteDocument(
            Changed, TmpPath / "CurvedBox.SLDPRT", allow_carrier=False
        )


# a shifted face plane changes the box offset and must decline
@PytestLib.mark.skipif(not KAddBoxRoot.is_dir(), reason="additive box corpus unavailable")
def TestBoxShift(TmpPath: FilePath) -> None:
    SourcePath = KAddBoxRoot / "AdditiveBox-1.1.4.FCStd"
    DocumentValue = OpenDocument(SourcePath)
    BrepValue = DocumentValue.brep
    assert BrepValue is not None
    SurfaceValue = BrepValue.surfaces[0]
    assert isinstance(SurfaceValue, PlaneSurface)
    Changed = ReplaceData(
        DocumentValue,
        brep=ReplaceData(
            BrepValue,
            surfaces=(
                ReplaceData(SurfaceValue, origin=VectorThree(1.0, 0.0, 0.0)),
                *BrepValue.surfaces[1:],
            ),
        ),
    )
    assert HasVendorPartEncoding(Changed) is False
    with PytestLib.raises(ApplicationUsabilityError):
        _ = WriteDocument(
            Changed, TmpPath / "ShiftedBox.SLDPRT", allow_carrier=False
        )


# refine false changes authored cleanup so the older schema must decline
@PytestLib.mark.skipif(not KAddBoxRoot.is_dir(), reason="additive box corpus unavailable")
def TestAddBoxNo(TmpPath: FilePath) -> None:
    SourcePath = KAddBoxRoot / "AdditiveBox-0.21.2.FCStd"
    DocumentValue = OpenDocument(SourcePath)
    assert HasVendorPartEncoding(DocumentValue) is False
    with PytestLib.raises(ApplicationUsabilityError):
        _ = WriteDocument(
            DocumentValue,
            TmpPath / f"{SourcePath.stem}.SLDPRT",
            allow_carrier=False,
        )
