# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# the receipt must distinguish a qualified typed prism from whole archive admission
def CheckPrismState(Value: object) -> None:
    assert Value == {
        "status": "returned_document",
        "feature_operation": "create",
        "sketch_constraints": [
            "horizontal",
            "vertical",
            "horizontal",
            "vertical",
            "coincident",
            "distance_x",
            "distance_y",
        ],
    }
