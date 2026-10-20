# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoRevisionTableDefsC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (12399, 4, 146, "primitive:int", 0),
            (12403, 4, 159, "primitive:int", 0),
            (12407, 4, 172, "primitive:int", 1),
            (12411, 4, 185, "primitive:int", 0),
            (12415, 4, 215, "primitive:int", 0),
        ),
    },
)
