from pathlib import Path as FilePath

from tests.Convert.Solidworks.Properties.ChangeTextPart import ChangeTextPart
from tests.Convert.Solidworks.Properties.MakeTextPart import MakeTextPart
from tests.Convert.Solidworks.Research.Resolved.RunPublicRead import RunPublicRead


# unsupported optional metadata must fail its complete projection while preserving the existing native geometry and history
def TestTextScope(TmpPath: FilePath) -> None:
    SourcePath = MakeTextPart(TmpPath / "ScopeText.SLDPRT")
    Baseline = RunPublicRead(SourcePath)
    FaultValues = (
        "equation",
        "type",
        "linked",
        "evaluated",
        "dictionary",
        "duplicate",
        "variant",
        "extra",
        "stale-id",
        "stale-owner",
        "malformed",
        "doctype",
        "utf16-doctype",
        "advanced-manager",
        "unknown-advanced-policy",
    )
    for FaultValue in FaultValues:
        Document = RunPublicRead(ChangeTextPart(SourcePath, FaultValue))
        InfoValue = Document.metadata["solidworks.part_text_properties"]
        assert isinstance(InfoValue, dict) and InfoValue["status"] == "unsupported"
        assert (
            "custom_properties" not in Document.metadata
            and "document_summary" not in Document.metadata
        )
        assert all(
            "custom_properties" not in Value.attributes
            for Value in Document.configurations
        )
        assert any(
            Value.code == "solidworks.part_text_properties_unavailable"
            for Value in Document.diagnostics
        )
        assert Document.feature_timeline == Baseline.feature_timeline
        assert (
            Document.sketches == Baseline.sketches
            and Document.parameters == Baseline.parameters
        )
        assert Document.bodies == Baseline.bodies
