from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Fillets.ReadFilletDrive import (
    ReadFilletDrive,
)


# history checks and public projection must use the same live radial value
def ReadFilletRad(FilletValue: ArchiveNode) -> float:
    return ReadFilletDrive(FilletValue).RadiusValue
