from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoDimPatternRegenStatusC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9180, 4, 4420, "primitive:long", 1),
            (9184, 4, 4436, "primitive:long", 0),
            (9188, 4, 4452, "primitive:long", 0),
            (9194, 4, 4637, "primitive:long", 0),
            (9198, 4, 4650, "primitive:long", 0),
            (11070, 1, 5937, "primitive:uchar", 1),
            (11073, 1, 6019, "primitive:uchar", 1),
            (11076, 8, 5488, "primitive:double", float.fromhex("0x0.0p+0")),
            (11084, 4, 5504, "primitive:long", 0),
            (11088, 4, 5520, "primitive:long", 0),
            (11092, 4, 5536, "primitive:long", 0),
            (11096, 4, 5552, "primitive:long", 0),
            (11100, 4, 5610, "primitive:long", 0),
            (11104, 4, 5626, "primitive:long", 0),
            (11112, 4, 5714, "primitive:long", 0),
            (11116, 4, 5730, "primitive:long", 0),
            (11120, 4, 5788, "primitive:long", 0),
            (11124, 4, 5804, "primitive:long", 0),
            (11132, 4, 6290, "primitive:long", 1),
            (11136, 4, 6348, "primitive:long", 0),
            (11140, 4, 6429, "primitive:long", 0),
            (11169, 4, 6764, "primitive:long", 0),
            (11173, 4, 6780, "primitive:long", 0),
            (11177, 4, 6796, "primitive:long", 351531744),
            (11181, 4, 6812, "primitive:long", 351678928),
            (11185, 4, 6890, "primitive:long", 0),
            (11189, 8, 8841, "primitive:double", float.fromhex("0x0.0p+0")),
            (11197, 4, 8865, "primitive:long", -1),
        ),
    },
)
