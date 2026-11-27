# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

# only discovery captures establish this repair without consuming qualification or holdout families
KDiscoveryCases = tuple(
    (RecipeName, VariantName)
    for RecipeName, Variants in (
        (
            "P01",
            (
                "baseline-a",
                "baseline-b",
                "edit-width_mm-41",
                "edit-height_mm-23",
                "units-inch",
                "plane-yz",
            ),
        ),
        (
            "P03",
            (
                "baseline-a",
                "baseline-b",
                "edit-width_mm-41",
                "edit-height_mm-23",
                "edit-depth_mm-12",
                "units-inch",
                "plane-yz",
                "direction-negative",
            ),
        ),
    )
    for VariantName in Variants
)
