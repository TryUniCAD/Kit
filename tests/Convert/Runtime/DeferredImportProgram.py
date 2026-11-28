# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# deferred exports must remain usable when only the checked source packages enter a fresh interpreter
KDeferredProgram = """import sys
sys.path.insert(0, sys.argv[1])
import convert
assert not hasattr(convert, 'AbsentModule')
assert 'AbsentModule' not in vars(convert)
assert 'convert.adapters.registry' not in sys.modules
assert 'CarrierReason' in dir(convert)
assert 'convert.adapters.registry.AdapterDiscovery' not in sys.modules
from convert import CarrierReason
from convert.adapters.base.TransferContract import CarrierReason as DeclaredReason
assert CarrierReason is DeclaredReason
from convert.adapters.solidworks import Core
assert 'convert.adapters.solidworks.Core.Writing' not in sys.modules
Writing = getattr(Core, 'Writing')
assert sys.modules['convert.adapters.solidworks.Core.Writing'] is Writing
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
assert Core.SldprtWriter is SldprtWriter
assert vars(Core)['SldprtWriter'] is SldprtWriter
from convert.adapters.registry.AdapterDiscovery import LoadExportMod
for ModuleName in ('socket', 'adsk.core', 'convert..api'):
    try:
        LoadExportMod(ModuleName)
    except ValueError:
        continue
    raise AssertionError('invalid deferred module was admitted: ' + ModuleName)
"""
