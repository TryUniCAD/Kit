# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.adapters.registry import AdapterRegistry


# dependency injection keeps adapter discovery replaceable without cad application coupling
def InitEngineMut(SelfValue, RegistryData: AdapterRegistry):
    setattr(SelfValue, "registry", RegistryData)
