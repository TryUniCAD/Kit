from __future__ import annotations

from interchange import CadDocument, frozen_mapping as FreezeMapping

from convert.adapters.base.ContractTypes import KSourceType as Source
from convert.adapters.base.ReadOptions import ReadOptions
from convert.api.ApiContext import KConvertEngine


# public reads centralize option construction so adapters receive one stable contract
def OpenDocument(
    SourceData: Source,
    *,
    SourceFormat: str | None = None,
    Configuration: str | None = None,
    IncludeBrep: bool = True,
    IncludeTess: bool = True,
    StrictMode: bool = True,
    IncludeNativeAppearance: bool = False,
) -> CadDocument:
    return KConvertEngine.read(
        SourceData,
        format_id=SourceFormat,
        options=ReadOptions(
            configuration=Configuration,
            include_brep=IncludeBrep,
            include_tessellation=IncludeTess,
            strict=StrictMode,
            values=FreezeMapping(
                {"include_native_appearance": True} if IncludeNativeAppearance else {}
            ),
        ),
    )
