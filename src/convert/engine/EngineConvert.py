from __future__ import annotations

from convert.adapters.base.ContractTypes import (
    KSourceType as Source,
    KTargetType as Destination,
)
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.base.WriteOptions import WriteOptions
from convert.engine.EngineResult import ConversionResult as ConvertResult
from convert.Formats.CheckSourceText import CheckSourceText
from convert.Formats.SourceFormat import ResolveFormat


# conversion orchestration stays isolated so registry read and write contracts remain reusable
class EngineConvert:

    # one neutral document boundary prevents direct coupling between independent format adapters
    def ConvertData(
        self,
        SourceData: Source,
        TargetData: Destination,
        *,
        SourceFormat: str | None = None,
        DestFormat: str | None = None,
        ReadOpts: ReadOptions | None = None,
        WriteOpts: WriteOptions | None = None,
    ) -> ConvertResult:
        RegistryData = getattr(self, "registry")
        ReadPolicy = ReadOpts or ReadOptions()
        DocumentData, ReaderData = RegistryData.read_with_adapter(
            SourceData,
            format_id=SourceFormat,
            options=ReadPolicy,
        )
        SourceName = ResolveFormat(DocumentData, ReaderData)
        if ReadPolicy.StrictMode:
            CheckSourceText(
                DocumentData, SourceName, TargetData, DestFormat, RegistryData
            )
        OutputResult = RegistryData.write(
            DocumentData,
            TargetData,
            format_id=DestFormat,
            options=WriteOpts or WriteOptions(),
        )
        return ConvertResult(
            document=DocumentData,
            output=OutputResult,
            source_format=SourceName,
            destination_format=OutputResult.adapter,
        )
