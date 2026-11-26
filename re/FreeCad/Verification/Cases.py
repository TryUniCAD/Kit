# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

KCases = {
    "restored": {
        "file": "RestoredForward.FCStd",
        "sha256": "c208eb140dc74464762a0db0b37368832c868d8040c54e7e6eec6dacb2fa2ffa",
        "mode": "inline",
        "parameters": [
            {"id": "depth:forward", "value": 11.0, "unit": "mm", "owner": "boss:fresh"},
            {"id": "depth:reverse", "value": 5.0, "unit": "mm", "owner": "boss:fresh"},
        ],
        "origin": "Restored/forward-restored.FCStd",
    },
    "forward-front": {
        "file": "ForwardFrontEdited.FCStd",
        "sha256": "6aa2d615697bea85dabd5e7d744ca316751901c6dd2f445fe2492fbbd2116506",
        "mode": "refused",
        "parameters": [],
        "origin": "SavedEdits/forward-depth_forward.FCStd",
    },
    "forward-rear": {
        "file": "ForwardRearEdited.FCStd",
        "sha256": "301219f9e6bba4a4d82daae94a67767ab9a08d879e7fc8e93f57f10fb54a727f",
        "mode": "refused",
        "parameters": [],
        "origin": "SavedEdits/forward-depth_reverse.FCStd",
    },
    "reversed-front": {
        "file": "ReversedFrontEdited.FCStd",
        "sha256": "74f0ff0e5eb6a0267b368b3fe1084c0a6d7fefc3035609ac012895382e291d32",
        "mode": "refused",
        "parameters": [],
        "origin": "SavedEdits/reversed-depth_forward.FCStd",
    },
    "reversed-rear": {
        "file": "ReversedRearEdited.FCStd",
        "sha256": "c86a24fe388c442dbbac9f79cab2c997210dcc4a5f3c5c1a080a976b26db4937",
        "mode": "refused",
        "parameters": [],
        "origin": "SavedEdits/reversed-depth_reverse.FCStd",
    },
    "symmetric": {
        "file": "SymmetricEdited.FCStd",
        "sha256": "f4c03d01d086946f963c52c37e41dd7e731acb55db360fc8af8fcd22bc9c832d",
        "mode": "refused",
        "parameters": [],
        "origin": "SavedEdits/symmetric-depth_total.FCStd",
    },
    "mixed": {
        "file": "AliasMixed.FCStd",
        "sha256": "225f7afebb1fea828b8abbd3c0867440201c9792f9c93baed52ebabe47b98066",
        "mode": "native",
        "parameters": [
            {
                "id": "freecad:parameter:AliasExtrusion:LengthFwd",
                "value": 11.0,
                "unit": "mm",
                "owner": "freecad:feature:AliasExtrusion",
                "expression": "DepthInputs.FrontCap",
                "targets": ["freecad:parameter:DepthInputs:cell:D4"],
            },
            {
                "id": "freecad:parameter:AliasExtrusion:LengthRev",
                "value": 5.0,
                "unit": "mm",
                "owner": "freecad:feature:AliasExtrusion",
                "expression": "DepthInputs.RearCap",
                "targets": ["freecad:parameter:DepthInputs:cell:B8"],
            },
            {
                "id": "freecad:parameter:DepthInputs:cell:D4",
                "value": 1.1,
                "unit": "cm",
                "owner": "freecad:object:DepthInputs",
            },
            {
                "id": "freecad:parameter:DepthInputs:cell:B8",
                "value": 5.0,
                "unit": "mm",
                "owner": "freecad:object:DepthInputs",
            },
        ],
        "origin": "Aliases/mixed.FCStd",
    },
    "equal": {
        "file": "AliasEqual.FCStd",
        "sha256": "ddcbc42179f2ed5497be363c96f8cb57366f916cfa8aaa5ba7cd0f9cd2fd58f7",
        "mode": "native",
        "parameters": [
            {
                "id": "freecad:parameter:AliasExtrusion:LengthFwd",
                "value": 7.0,
                "unit": "mm",
                "owner": "freecad:feature:AliasExtrusion",
                "expression": "DepthInputs.FrontCap",
                "targets": ["freecad:parameter:DepthInputs:cell:B9"],
            },
            {
                "id": "freecad:parameter:AliasExtrusion:LengthRev",
                "value": 7.0,
                "unit": "mm",
                "owner": "freecad:feature:AliasExtrusion",
                "expression": "DepthInputs.RearCap",
                "targets": ["freecad:parameter:DepthInputs:cell:A2"],
            },
            {
                "id": "freecad:parameter:DepthInputs:cell:B9",
                "value": 7.0,
                "unit": "mm",
                "owner": "freecad:object:DepthInputs",
            },
            {
                "id": "freecad:parameter:DepthInputs:cell:A2",
                "value": 0.7,
                "unit": "cm",
                "owner": "freecad:object:DepthInputs",
            },
        ],
        "origin": "Aliases/equal_reordered.FCStd",
    },
    "edited": {
        "file": "AliasEdited.FCStd",
        "sha256": "cec3b5e0a0936c7e14e48078ee0657697f0df774ca6af326a5e7f96ea38a4055",
        "mode": "native",
        "parameters": [
            {
                "id": "freecad:parameter:AliasExtrusion:LengthFwd",
                "value": 14.0,
                "unit": "mm",
                "owner": "freecad:feature:AliasExtrusion",
                "expression": "DepthInputs.FrontCap",
                "targets": ["freecad:parameter:DepthInputs:cell:D4"],
            },
            {
                "id": "freecad:parameter:AliasExtrusion:LengthRev",
                "value": 5.0,
                "unit": "mm",
                "owner": "freecad:feature:AliasExtrusion",
                "expression": "DepthInputs.RearCap",
                "targets": ["freecad:parameter:DepthInputs:cell:B8"],
            },
            {
                "id": "freecad:parameter:DepthInputs:cell:D4",
                "value": 14.0,
                "unit": "mm",
                "owner": "freecad:object:DepthInputs",
            },
            {
                "id": "freecad:parameter:DepthInputs:cell:B8",
                "value": 5.0,
                "unit": "mm",
                "owner": "freecad:object:DepthInputs",
            },
        ],
        "origin": "Aliases/edited.FCStd",
    },
}
