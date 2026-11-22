from convert.adapters.solidworks.Archive.Construction.Dimensions.LinearStyle import (
    LinearStyle,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.ReadModelLinear import (
    ReadModelLinear,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    RequireNode,
)


# native distance display initialization projects the filed assembly linear style rather than an unrelated null document default
def ReadLinearStyle(Assembly: ArchiveNode) -> LinearStyle:
    _ = RequireNode(Assembly, "moAssembly_c")
    return ReadModelLinear(Assembly)
