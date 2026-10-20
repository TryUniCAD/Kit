# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoAngOrdinateDimDefC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (8349, 4, 169, "primitive:int", 1),
            (8353, 4, 185, "primitive:int", 21),
            (8357, 4, 201, "primitive:int", 0),
            (8361, 4, 217, "primitive:int", 0),
            (8365, 4, 233, "primitive:int", 0),
        ),
    },
)
