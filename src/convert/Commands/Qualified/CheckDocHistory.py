# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.document.Models.DocumentModel import CadDocument


# comparison agreement must not promote documents that lack editable feature history
def CheckDocHistory(Document: CadDocument) -> None:
    if not Document.feature_timeline:
        raise ValueError(
            "MissingFeatureHistory records are not conversion-ready; "
            + "use kit decode or kit research for inspection"
        )
