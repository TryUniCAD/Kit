from pathlib import Path

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.Staging.WriteWholeMut import WriteWholeMut


# the payload operation needs a consistent construction rule so public document claims remain grounded in native records
def WritePayloadMut(
    Target: KTargetType, Payload: bytes, Settings: WriteOptions
) -> Path | None:
    if isinstance(Target, (str, Path)):
        PathValue = Path(Target)
        with PathValue.open("wb" if Settings.overwrite else "xb") as Stream:
            Count = Stream.write(Payload)
        if Count != len(Payload):
            raise OSError("Incomplete Fusion file write")
        return PathValue
    WriteWholeMut(Target, Payload)
    return None
