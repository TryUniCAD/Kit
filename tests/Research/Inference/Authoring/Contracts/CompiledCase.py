# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import TypedDict


# native edits retain numeric driving values rather than opaque untyped metadata
class ProgramEdit(TypedDict):
    parameter: str
    value: float


# native variants retain their independent archive names in prepared path rosters
class ProgramVariant(TypedDict):
    name: str


# archive preparation consumes only the program lists that determine saved native files
class CaseProgram(TypedDict):
    edits: list[ProgramEdit]
    variants: list[ProgramVariant]


# compiled case options retain the source program needed for native archive preparation
class CaseOptions(TypedDict):
    program: CaseProgram


# research compiler output carries one canonical recipe and its explicit driving inputs
class CompiledCase(TypedDict):
    recipe: str
    parameters: dict[str, float]
    options: CaseOptions
