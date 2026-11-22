from collections.abc import Mapping
from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.TransferContract import CapTransfer
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.Staging.WriteWholeMut import WriteWholeMut


# exact measured part bytes must occupy one standalone destination before the result is qualified
def PublishMeasMut(
    TargetValue: KTargetType,
    OutputPath: FilePath | None,
    SettingsValue: WriteOptions,
    Payload: bytes,
    Evidence: Mapping[str, object],
    Transfers: tuple[CapTransfer, ...] = (),
) -> WriteResult:
    if OutputPath is None:
        WriteWholeMut(TargetValue, Payload)
    else:
        with OutputPath.open("wb" if SettingsValue.overwrite else "xb") as OutputFile:
            if OutputFile.write(Payload) != len(Payload):
                raise OSError("short measured native part write")
    return WriteResult(
        OutputPath,
        KPartFormatId,
        len(Payload),
        metadata=Evidence,
        transfers=Transfers,
        vendor_loadable=True,
        application_usable=True,
    )
