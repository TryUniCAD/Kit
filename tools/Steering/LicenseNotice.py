# mandatory legal text stays exact because general license prefixes must not bypass comment policy
KRequiredNotice = (
    "# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0",
    "# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt",
    "#",
    "# This SPDX license identifier and copyright notice must not be",
    "# removed, altered, or obscured. Doing so is a material breach of",
    "# the PolyForm Strict License 1.0.0 and voids all licenses granted",
    "# to you under it immediately and permanently.",
)


# historical legal ownership remains mandatory when the workspace explicitly requires its original notice
KOriginalNotice = (
    KRequiredNotice[0],
    "# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin",
    *KRequiredNotice[2:],
)


# only the complete leading notice may survive because misplaced or altered commentary remains prohibited
def GetNoticeLines(SourceText: str) -> set[tuple[int, int]]:
    SourceLines = SourceText.replace("\r\n", "\n").split("\n")
    FirstLine = int(SourceLines[0].startswith("#!"))
    AfterLine = FirstLine + len(KRequiredNotice)
    if tuple(SourceLines[FirstLine:AfterLine]) not in (
        KRequiredNotice,
        KOriginalNotice,
    ):
        return set()
    return {(LineNum, 0) for LineNum in range(FirstLine + 1, AfterLine + 1)}
