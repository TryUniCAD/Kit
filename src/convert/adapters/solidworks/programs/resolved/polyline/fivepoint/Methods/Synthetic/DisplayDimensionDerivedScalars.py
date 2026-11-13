from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Synthetic.DisplayDimensionDerivedScalars import (
    KOwnerSites,
)


KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (
                10596,
                8,
                "DisplayDimensionOneDerivedScalar",
                "direct:d",
                float.fromhex("0x1.26e978d4fdf3bp-7"),
            ),
        ),
    },
)
