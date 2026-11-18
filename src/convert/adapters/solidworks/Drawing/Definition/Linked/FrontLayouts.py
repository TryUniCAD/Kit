from types import MappingProxyType

from convert.adapters.solidworks.Drawing.Definition.Emission.Layouts.BlankLayouts import (
    KBlankLayouts,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.CompFields import (
    KCompFields,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.SupportFields import (
    KSupportFields,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.ViewFields import (
    KViewFields,
)

# a linked profile must preserve the exact blank layout while adding independently proved view owners
KFrontLayouts = MappingProxyType(
    {
        **KBlankLayouts,
        **KViewFields,
        **KSupportFields,
        **KCompFields,
        "moScaleSysScale_c": (),
    }
)
