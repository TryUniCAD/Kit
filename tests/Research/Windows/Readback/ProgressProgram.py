# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from pathlib import Path as FilePath

# managed journal actions live in the same powershell source type used by the fixture process
KProgressScript = (
    FilePath(__file__).with_name("ProgressFixture.ps1").read_text(encoding="utf-8")
)
