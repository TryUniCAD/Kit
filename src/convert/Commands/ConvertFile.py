from convert.api.ApiContext import GetRegistry
from convert.api.ApiOpen import OpenDocument
from convert.api.ApiWrite import WriteDocument
from convert.Commands.CheckPortable import CheckPortable
from convert.Commands.CliOptions import CliOptions
from convert.Commands.WriteReport import WriteReport
from convert.formats.SourceFormat import ResolveFormat


def ConvertFile(Options: CliOptions) -> dict[str, object]:
    if Options.Destination is None:
        raise ValueError("Conversion requires a destination")
    Registry = GetRegistry()
    Reader = (
        Registry.GetReader(Options.SourceFormat)
        if Options.SourceFormat
        else Registry.PickReader(Options.Source)
    )
    Document = OpenDocument(
        Options.Source,
        SourceFormat=Reader.info.FormatId,
        Configuration=Options.Configuration,
        StrictMode=True,
    )
    CheckPortable(Document)
    Result = WriteDocument(
        Document,
        Options.Destination,
        DestFormat=Options.DestFormat,
        Configuration=Options.Configuration,
        Overwrite=Options.Overwrite,
        ValidateData=True,
        AllowCarrier=False,
    )
    return {
        "source_format": ResolveFormat(Document, Reader),
        "destination_format": Result.AdapterName,
        **WriteReport(Result),
    }
