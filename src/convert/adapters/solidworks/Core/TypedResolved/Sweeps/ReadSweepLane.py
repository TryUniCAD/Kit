from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Cold.IsColdSweep import (
    IsColdSweep,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Cold.ReadColdSw import (
    ReadColdSw,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwPart import (
    IsSavedSweep,
    ReadSwPart,
)
from interchange.document.Models.DocumentModel import CadDocument


# saved topology owns its own lane and raw extraction bypasses analytic reconstruction
def ReadSweepLane(
    Archive: SldprtArchive, DataValue: bytes, Label: str, Settings: ReadOptions
) -> CadDocument | None:
    if Settings.extract_raw_brep:
        return None
    IsSaved = IsSavedSweep(Archive, Settings.configuration)
    if not IsSaved and not IsColdSweep(Archive, Settings.configuration):
        return None
    try:
        if IsSaved:
            return ReadSwPart(Archive, DataValue, Label, Settings)
        return ReadColdSw(Archive, DataValue, Label, Settings.include_brep)
    except SldprtFormatError:
        if Settings.strict:
            raise
    return None
