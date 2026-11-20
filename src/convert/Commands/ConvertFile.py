from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.base.WriteOptions import WriteOptions
from convert.api.ApiContext import GetRegistry
from convert.api.ApiValues import BuildWriteVals
from convert.Commands.CheckPortable import CheckPortable
from convert.Commands.CliOptions import CliOptions
from convert.Commands.WriteReport import WriteReport
from convert.Formats.SourceFormat import ResolveFormat


# file conversion must preserve reader identity while enforcing portable data and native writer policy
def ConvertFile(Options: CliOptions) -> dict[str, object]:
    if Options.Destination is None:
        raise ValueError("Conversion requires a destination")
    Registry = GetRegistry()
    DestFormat = Options.DestFormat
    if DestFormat is None:
        Writers = tuple(
            Adapter
            for Adapter in Registry.GetWriters()
            if Options.Destination.suffix.casefold()
            in {Extension.casefold() for Extension in Adapter.info.Extensions}
        )
        if not Writers:
            raise ValueError(
                "no writer supports the destination suffix; use --to FORMAT"
            )
        if len(Writers) != 1:
            raise ValueError("Destination suffix is ambiguous; use --to FORMAT")
        DestFormat = Writers[0].info.FormatId
    ReadOpts = ReadOptions(configuration=Options.Configuration, strict=True)
    Document, Reader = Registry.ReadAdapter(
        Options.Source,
        FormatId=Options.SourceFormat,
        ReadOpts=ReadOpts,
    )
    CheckPortable(Document)
    Result = Registry.WriteFromRead(
        Document,
        Options.Destination,
        Reader,
        ReadOpts,
        FormatId=DestFormat,
        WriteOpts=WriteOptions(
            configuration=Options.Configuration,
            overwrite=Options.Overwrite,
            validate=True,
            values=BuildWriteVals({"require_native_transfers": True}, False),
        ),
    )
    return {
        "source_format": ResolveFormat(Document, Reader),
        "destination_format": Result.AdapterName,
        **WriteReport(Result),
    }
