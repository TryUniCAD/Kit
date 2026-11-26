# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

# independent catalogue identities prevent registry expansion from silently broadening executable coverage
KRecipeTargets = {
    "extrude-two-direction": "family:extrude:two-direction-extrude",
    "extrude-midplane": "family:extrude:midplane-extrude",
    "extrude-offset-start": "family:extrude:offset-start-extrude",
    "extrude-thin": "family:extrude:thin-extrude",
    "extrude-up-to": "family:extrude:up-to-geometry-extrude",
    "revolve-two-direction": "family:revolve:two-direction-revolve",
    "revolve-midplane": "family:revolve:midplane-revolve",
    "revolve-thin": "family:revolve:thin-revolve",
    "revolve-cut": "family:revolve:cut-revolve",
}

# unsupported written recipes must remain visible beside registered and legacy cases
KExtraFeatures = (
    "family:sketchlines:corner-rectangle",
    "family:sketchdimensions:linear-dimension",
    "family:sketchdimensions:diameter-dimension",
    "family:sketchconics:circle",
    "family:extrude:boss-base-extrude",
    "family:extrude:cut-extrude",
    "family:revolve:boss-base-revolve",
    "family:extrude:surface-extrude",
    "family:revolve:surface-revolve",
    "family:fillet:constant-radius-fillet",
)
