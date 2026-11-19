from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import (
    ReadChildStamp,
)
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarContext import (
    PlanarContext,
    PlanarChild,
)
from convert.adapters.solidworks.Assembly.Assembly import NativeAsmItem
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CylChild import CylChild


# selected cylinder stamps must identify the actual loaded child configuration rather than a plausible cache epoch
def ReadCylStamp(
    Context: PlanarContext,
    ChildValue: CylChild,
    ItemValue: NativeAsmItem,
    Wrapper: ArchiveNode,
    Occurrence: ArchiveNode,
) -> int:
    Definition = Context.DefinitionMap[ItemValue.definition_id]
    SourceName = PureWindowsPath(Definition.source_path).name.casefold()
    return ReadChildStamp(
        Wrapper,
        Occurrence,
        PlanarChild(ChildValue.LinkValue.ConfigValue.HeaderValue, {}),
        ItemValue.configuration_id,
        ItemValue.configuration_name,
        SourceName,
    )
