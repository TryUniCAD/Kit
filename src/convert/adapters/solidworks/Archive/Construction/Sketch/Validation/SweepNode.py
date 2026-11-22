from __future__ import annotations

from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepEdge import (
    SweepEdge,
)


# balanced sweep membership needs explicit topology without borrowing archive graph identities
@DataClass(eq=False, slots=True)
class SweepNode:
    EdgeValue: SweepEdge
    ParentValue: SweepNode | None = None
    LeftValue: SweepNode | None = None
    RightValue: SweepNode | None = None
    HeightValue: int = 1
