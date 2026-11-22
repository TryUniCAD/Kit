# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from importlib import import_module as ImportModule


# research modules remain runtime dependencies while callers declare their precise exercised contracts
def LoadSymbol(ModuleName: str, SymbolName: str) -> object:
    return getattr(ImportModule(ModuleName), SymbolName)
