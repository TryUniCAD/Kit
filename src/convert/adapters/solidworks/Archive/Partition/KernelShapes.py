from types import MappingProxyType

from convert.adapters.solidworks.Archive.Partition.Fields.AnalyticShapes import (
    KAnalyticShapes,
)
from convert.adapters.solidworks.Archive.Partition.Fields.AttributeShapes import (
    KAttributeShapes,
)
from convert.adapters.solidworks.Archive.Partition.Fields.BoundaryShapes import (
    KBoundaryShapes,
)
from convert.adapters.solidworks.Archive.Partition.Fields.SolidShapes import (
    KSolidShapes,
)
from convert.adapters.solidworks.Archive.Partition.Fields.WorldShapes import (
    KWorldShapes,
)

# ordinary current partitions admit only source mapped kernel classes in this grammar
KKernelShapes = MappingProxyType(
    {
        **KWorldShapes,
        **KSolidShapes,
        **KBoundaryShapes,
        **KAnalyticShapes,
        **KAttributeShapes,
    }
)
