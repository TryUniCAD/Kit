from __future__ import annotations

from pathlib import Path as FilePath

import pytest as PytestLib

from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
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
    for NameValue in ("AdditiveBox-1.1.4.FCStd", "AdditiveBox-0.21.2.FCStd"):
        SourcePath = KAddBoxRoot / NameValue
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
