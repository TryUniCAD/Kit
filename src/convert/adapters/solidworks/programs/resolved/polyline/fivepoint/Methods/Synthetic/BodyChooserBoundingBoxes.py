from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Synthetic.BodyChooserBoundingBoxes import (
    KOwnerSites,
)


KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (8839, 4, "BoundingBoxOnePerBodyChooserIndex", "direct:i", 0),
            (9069, 4, "BoundingBoxTwoPerBodyChooserIndex", "direct:i", 0),
        ),
    },
)
