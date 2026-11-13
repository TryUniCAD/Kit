from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgEntHandle.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5388, 2, 664, "primitive:ushort", 0),
            (5390, 4, 830, "primitive:long", -1),
            (5394, 4, 928, "primitive:long", 0),
            (6159, 2, 664, "primitive:ushort", 0),
            (6161, 4, 830, "primitive:long", -1),
            (6165, 4, 928, "primitive:long", 0),
            (6171, 2, 664, "primitive:ushort", 4),
            (6173, 4, 830, "primitive:long", -1),
            (6177, 4, 928, "primitive:long", 0),
            (6321, 2, 664, "primitive:ushort", 0),
            (6323, 4, 830, "primitive:long", -1),
            (6327, 4, 928, "primitive:long", 0),
            (6333, 2, 664, "primitive:ushort", 1),
            (6335, 4, 830, "primitive:long", -1),
            (6339, 4, 928, "primitive:long", 0),
            (6483, 2, 664, "primitive:ushort", 1),
            (6485, 4, 830, "primitive:long", -1),
            (6489, 4, 928, "primitive:long", 0),
            (6495, 2, 664, "primitive:ushort", 2),
            (6497, 4, 830, "primitive:long", -1),
            (6501, 4, 928, "primitive:long", 0),
            (6645, 2, 664, "primitive:ushort", 2),
            (6647, 4, 830, "primitive:long", -1),
            (6651, 4, 928, "primitive:long", 0),
            (6657, 2, 664, "primitive:ushort", 3),
            (6659, 4, 830, "primitive:long", -1),
            (6663, 4, 928, "primitive:long", 0),
            (6807, 2, 664, "primitive:ushort", 3),
            (6809, 4, 830, "primitive:long", -1),
            (6813, 4, 928, "primitive:long", 0),
            (6819, 2, 664, "primitive:ushort", 4),
            (6821, 4, 830, "primitive:long", -1),
            (6825, 4, 928, "primitive:long", 0),
            (6965, 2, 13748, "primitive:ushort", 0),
            (7057, 2, 13748, "primitive:ushort", 0),
            (7149, 2, 13748, "primitive:ushort", 0),
            (7241, 2, 13748, "primitive:ushort", 0),
            (7333, 2, 13748, "primitive:ushort", 0),
        ),
    },
)
