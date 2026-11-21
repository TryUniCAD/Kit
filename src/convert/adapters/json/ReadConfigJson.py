from dataclasses import replace as Replace

from interchange.document.Models.DocumentModel import CadDocument
from interchange.serialization.JsonCodec import LoadJson


# explicit configuration reads must validate the requested complete graph before filtering
def ReadConfigJson(TextValue: str, ConfigName: str) -> CadDocument:
    Document = LoadJson(TextValue)
    if not isinstance(Document, CadDocument):
        raise TypeError("JSON does not describe a CadDocument")
    Matches = {
        Config.id
        for Config in Document.configurations
        if ConfigName in {Config.id, Config.name}
    }
    if not Matches:
        raise ValueError(f"configuration {ConfigName!r} is unavailable")
    Selected = Replace(
        Document,
        configurations=tuple(
            Replace(Config, active=Config.id in Matches)
            for Config in Document.configurations
        ),
    )
    Selected.assert_valid()
    return Selected
