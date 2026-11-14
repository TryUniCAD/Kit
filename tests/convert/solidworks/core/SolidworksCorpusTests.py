from __future__ import annotations

from pathlib import Path as FilePath

import pytest as PytestLib

from convert import open_document as OpenDocument
from convert import write_document as WriteDocument

# tracked v8 directory gives every part a real read and write boundary
KCorpusRoot = (
    FilePath(__file__).resolve().parents[4]
    / "re"
    / "solidworks"
    / "examples"
    / "Single Turbo Dual Overhead Cam V8 - KDP - 2024"
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
