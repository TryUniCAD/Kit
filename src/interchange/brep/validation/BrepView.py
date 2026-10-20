# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from typing import Any as AnyValue
from typing import Protocol as TypeProtocol


# the validation view decouples topology storage from independent diagnostic passes
class BrepView(TypeProtocol):
    Curves: tuple[AnyValue, ...]
    Pcurves: tuple[AnyValue, ...]
    Surfaces: tuple[AnyValue, ...]
    Vertices: tuple[AnyValue, ...]
    Edges: tuple[AnyValue, ...]
    Coedges: tuple[AnyValue, ...]
    Loops: tuple[AnyValue, ...]
    Wires: tuple[AnyValue, ...]
    Faces: tuple[AnyValue, ...]
    FaceUses: tuple[AnyValue, ...]
    Shells: tuple[AnyValue, ...]
    ShellUses: tuple[AnyValue, ...]
    Regions: tuple[AnyValue, ...]
    Bodies: tuple[AnyValue, ...]
    SchemaVersion: str
