from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoDynSurfIdArr.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (8422, 4, 4583, "primitive:long", 0),
            (8426, 4, 4596, "primitive:long", 0),
            (8635, 4, 4583, "primitive:long", 1),
            (8639, 4, 4596, "primitive:long", 0),
        ),
    },
)
