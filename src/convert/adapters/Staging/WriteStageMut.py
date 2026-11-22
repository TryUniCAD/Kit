from pathlib import Path as FilePath

from convert.adapters.base.AdapterProtocols import CadWriterAdapter
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WritePolicy import RunCheckedMut
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.Staging.PathStageOwner import KPathStageOwner
from interchange.document.Models.DocumentModel import CadDocument


# only the current registry managed write may associate a staged child with its final path
def WriteStageMut(
    DocumentValue: CadDocument,
    AdapterValue: CadWriterAdapter,
    StageValue: FilePath,
    FinalValue: FilePath,
    OptionsValue: WriteOptions,
    AllowCarrier: bool,
    NeedSelfContained: bool,
) -> WriteResult:
    TokenValue = KPathStageOwner.set((StageValue, FinalValue))
    try:
        return RunCheckedMut(
            DocumentValue,
            AdapterValue,
            StageValue,
            OptionsValue,
            AllowCarrier,
            NeedSelfContained,
        )
    finally:
        KPathStageOwner.reset(TokenValue)
