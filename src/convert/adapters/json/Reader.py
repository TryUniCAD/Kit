from convert.adapters.base import ReadOptions
from convert.adapters.base import Source
from convert.adapters.json.ReadConfigJson import ReadConfigJson
from convert.adapters.json.StreamIo import ReadText
from interchange import CadDocument
from interchange import filter_document as FilterDocument


# this mixin isolates filtering and validation from probing behavior
class JsonReader:

    # this reader restores filters and validates one interchange document
    def ReadAction(
        self, SourceValue: Source, Options: ReadOptions | None = None
    ) -> CadDocument:
        Settings = Options or ReadOptions()
        TextValue = ReadText(SourceValue)
        Document = (
            CadDocument.from_json(TextValue)
            if Settings.configuration is None
            else ReadConfigJson(TextValue, Settings.configuration)
        )
        Document = FilterDocument(
            Document,
            include_brep=Settings.include_brep,
            include_tessellation=Settings.include_tessellation,
            keep_payload_records=False,
        )
        if Settings.strict:
            Document.assert_valid()
        return Document
