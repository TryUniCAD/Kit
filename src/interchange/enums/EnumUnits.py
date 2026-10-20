# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.enums.EnumBase import WireEnum


# unit identity prevents adapters from silently changing dimensional interpretation
class UnitSystem(WireEnum):
    KMillimeter = "mm"
    KMeter = "m"
    KInch = "in"
