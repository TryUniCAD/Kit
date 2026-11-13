from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoPTSRefPlnDataC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (3557, 4, 13789, "primitive:long", 5),
            (3561, 4, 13960, "primitive:long", 0),
            (3567, 4, 14109, "primitive:long", 0),
            (4076, 4, 13789, "primitive:long", 5),
            (4080, 4, 13960, "primitive:long", 0),
            (4086, 4, 14109, "primitive:long", 0),
            (4646, 4, 13789, "primitive:long", 5),
            (4650, 4, 13960, "primitive:long", 0),
            (4656, 4, 14109, "primitive:long", 0),
            (8829, 4, 3225, "primitive:long", 0),
            (8833, 4, 3238, "primitive:long", 0),
            (8843, 4, 3355, "primitive:long", 0),
            (9059, 4, 3225, "primitive:long", 0),
            (9063, 4, 3238, "primitive:long", 0),
            (9073, 4, 3355, "primitive:long", 0),
        ),
    },
)
