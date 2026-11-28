from interchange.document.Models.DocumentModel import CadDocument


# exact dictionaries and the actual configuration identity must survive public readback without scope inheritance
def CheckTextPart(Document: CadDocument) -> None:
    assert Document.metadata["document_summary"] == {
        "title": "Fixture <α>",
        "author": "Reader control",
        "comments": "Authored comment",
    }
    assert Document.metadata["custom_properties"] == {
        "SharedName": "Document & α",
        "SecondText": "Literal text",
        "SpacedText": "  retained  ",
    }
    (ConfigValue,) = Document.configurations
    assert ConfigValue.name == "modeled default"
    assert ConfigValue.attributes["native_configuration_id"] == 0
    assert ConfigValue.attributes["custom_properties"] == {
        "SharedName": "Configuration <β>"
    }
    InfoValue = Document.metadata["solidworks.part_text_properties"]
    assert isinstance(InfoValue, dict) and InfoValue["status"] == "complete"
    assert Document.feature_timeline and Document.sketches and Document.parameters
