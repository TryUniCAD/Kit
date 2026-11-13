from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoDisplayItemC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9230, 2, 7611, "primitive:ushort", 0),
            (9238, 4, 7807, "primitive:long", 0),
            (9242, 4, 7975, "primitive:long", 0),
            (9267, 4, 8174, "primitive:long", 0),
            (9273, 4, 8364, "primitive:long", 0),
            (9277, 4, 8645, "primitive:long", 19000),
            (9281, 4, 1016, "primitive:long", 0),
            (9285, 4, 1055, "primitive:long", 524416),
            (9317, 4, 1275, "primitive:long", 0),
            (9339, 8, 1604, "primitive:double", float.fromhex("0x0.0p+0")),
            (9381, 4, 1652, "primitive:long", 1),
            (9385, 4, 1697, "primitive:long", 200),
            (9389, 1, 1919, "primitive:uchar", 0),
            (9390, 8, 2012, "primitive:double", float.fromhex("0x0.0p+0")),
            (9398, 4, 2025, "primitive:long", 0),
            (9402, 4, 2143, "primitive:long", 0),
            (9408, 8, 2348, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
            (9416, 4, 2698, "primitive:long", 0),
            (9420, 4, 3749, "primitive:long", 1),
            (9430, 4, 3790, "primitive:long", 0),
            (9434, 4, 3806, "primitive:long", 1),
            (9444, 4, 3847, "primitive:long", 0),
            (9448, 4, 3987, "primitive:long", 0),
            (9452, 4, 4003, "primitive:long", 0),
            (9456, 4, 4020, "primitive:long", -1),
            (9460, 4, 4049, "primitive:long", -1),
            (9468, 4, 4316, "primitive:long", 1),
            (9472, 4, 4332, "primitive:long", 0),
            (9482, 4, 4370, "primitive:long", 0),
            (9486, 4, 4454, "primitive:long", 0),
            (9490, 4, 4939, "primitive:long", 0),
            (9494, 4, 5239, "primitive:long", 0),
            (9498, 4, 5634, "primitive:long", 4),
            (9598, 4, 5809, "primitive:long", 2),
            (9618, 8, 5864, "primitive:double", float.fromhex("0x0.0p+0")),
            (9642, 8, 5864, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
