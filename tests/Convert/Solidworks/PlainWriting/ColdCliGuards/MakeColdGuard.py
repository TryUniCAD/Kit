from dataclasses import replace as CopyData

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Features.FeatureKinds import NativeFeature
from interchange.Features.FeatureStep import FeatureStep
from tests.Convert.Solidworks.PlainWriting.ColdCliGuards.MakeColdAsm import MakeColdAsm
from tests.Convert.Solidworks.PlainWriting.ColdCliGuards.MakeFakeCold import (
    MakeFakeCold,
)


# every cold delegation negative must retain valid neutral structure while changing required source meaning
def MakeColdGuard(Document: CadDocument, ModeName: str, RoleName: str) -> CadDocument:
    if ModeName == "fake":
        return MakeFakeCold(Document, RoleName)
    if ModeName == "binding":
        return CopyData(Document, source=CopyData(Document.source, sha256="0" * 64))
    if ModeName == "feature":
        Feature = FeatureStep(
            "injected/feature",
            "Unmodeled",
            FeatureKind.KNative,
            max(Value.order for Value in Document.feature_timeline) + 1,
            definition=NativeFeature("solidworks.sldprt", "unmodeled"),
        )
        return CopyData(
            Document, feature_timeline=(*Document.feature_timeline, Feature)
        )
    if ModeName == "metadata":
        return CopyData(
            Document,
            metadata={**Document.metadata, "opaque_owner": b"unmodeled native state"},
        )
    if ModeName in ("assembly", "embedded"):
        return CopyData(
            Document, assembly=MakeColdAsm(Document, ModeName == "embedded")
        )
    raise ValueError("unknown cold delegation guard case")
