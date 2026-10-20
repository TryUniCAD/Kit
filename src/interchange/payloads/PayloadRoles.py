# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.enums.EnumBase import WireEnum


# payload roles distinguish representations so filtering never guesses from filenames
class PayloadRole(WireEnum):
    KBrep = "brep"
    KTessellation = "tessellation"
    KFeatureHistory = "feature_history"
    KAssemblyStructure = "assembly_structure"
    KDocument = "document"
    KVerification = "verification"
    KAuxiliary = "auxiliary"
