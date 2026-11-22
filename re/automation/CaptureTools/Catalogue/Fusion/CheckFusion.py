# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from CaptureTools.Catalogue.Fusion.CheckReading import CheckReading


# recomputation must precede evidence so cached geometry cannot stand in for live parameters
def CheckFusion(Helper, Document, Case):
    if Helper["design_of"](Document).computeAll() is not True:
        raise RuntimeError("fusion refused native recomputation")
    Reading = Helper["measure"](Document, "catalogue authored parameter verification")
    return CheckReading(Reading, Case)
