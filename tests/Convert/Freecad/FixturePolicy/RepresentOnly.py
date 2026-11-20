# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace

from interchange.document.Models.DocumentModel import CadDocument
from tests.Interchange.Fixtures.DocumentFixture import BuildDocument


# representation and sketch codecs need isolated coverage without an unrelated feature reconstruction requirement
def RepresentOnly() -> CadDocument:
    return Replace(BuildDocument(), feature_timeline=(), bodies=())
