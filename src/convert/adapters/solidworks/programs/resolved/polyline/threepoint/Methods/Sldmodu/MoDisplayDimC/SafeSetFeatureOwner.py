from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoDisplayDimC.SafeSetFeatureOwner import (
    KOwnerSites,
)

KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5622, 4, 4836, "primitive:ulong", 0),
            (5626, 4, 4856, "primitive:long", 0),
            (5630, 4, 1917, "primitive:long", 3),
            (5635, 4, 2371, "primitive:long", 0),
            (5645, 4, 3383, "primitive:ulong", 100000),
            (7105, 4, 4836, "primitive:ulong", 1),
            (7109, 4, 4856, "primitive:long", 1),
            (7208, 4, 1917, "primitive:long", 3),
            (7213, 4, 2371, "primitive:long", 0),
            (7223, 4, 3383, "primitive:ulong", 100000),
        ),
    },
)
