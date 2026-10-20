# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Synthetic.AssemblyConfigurationArchivePrefix import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (0, 2, "AssemblyConfigurationArchivePrefix", "direct:H", 65535),
        ),
    },
)
