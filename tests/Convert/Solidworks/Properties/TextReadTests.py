from pathlib import Path as FilePath

from tests.Convert.Solidworks.Properties.ChangeTextPart import ChangeTextPart
from tests.Convert.Solidworks.Properties.CheckTextPart import CheckTextPart
from tests.Convert.Solidworks.Properties.MakeTextPart import MakeTextPart
from tests.Convert.Solidworks.Research.Resolved.RunPublicRead import RunPublicRead


# normal and stale binary cache archives must expose the same exact live text dictionaries in fresh public processes
def TestTextRead(TmpPath: FilePath) -> None:
    SourcePath = MakeTextPart(TmpPath / "FreshText.SLDPRT")
    CheckTextPart(RunPublicRead(SourcePath))
    CheckTextPart(RunPublicRead(ChangeTextPart(SourcePath, "stale-cache")))
    CheckTextPart(RunPublicRead(ChangeTextPart(SourcePath, "empty-advanced-manager")))


# property free native files must preserve their existing geometry path without adding a property qualification claim
def TestNoTextPart(TmpPath: FilePath) -> None:
    SourcePath = MakeTextPart(TmpPath / "NoText.SLDPRT", False)
    Document = RunPublicRead(SourcePath)
    assert "solidworks.part_text_properties" not in Document.metadata
    assert "custom_properties" not in Document.metadata
    assert "document_summary" not in Document.metadata
    assert Document.feature_timeline and Document.sketches and Document.parameters


# each explicit empty scope must survive a fresh public read without adding an absent owner
def TestEmptyText(TmpPath: FilePath) -> None:
    SourcePath = MakeTextPart(
        TmpPath / "EmptyText.SLDPRT",
        False,
        EmptyScopes=frozenset({"summary", "configuration"}),
    )
    Document = RunPublicRead(SourcePath)
    assert Document.metadata["document_summary"] == {}
    assert "custom_properties" not in Document.metadata
    (ConfigValue,) = Document.configurations
    assert ConfigValue.attributes["custom_properties"] == {}
    InfoValue = Document.metadata["solidworks.part_text_properties"]
    assert isinstance(InfoValue, dict) and InfoValue["configuration_ids"] == (0,)
    assert Document.feature_timeline and Document.sketches and Document.parameters
