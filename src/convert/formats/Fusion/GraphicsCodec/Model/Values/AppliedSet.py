from __future__ import annotations
from dataclasses import dataclass as MakeDataClass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Model.Values.SceneSet import SceneSet


@MakeDataClass(frozen=True, slots=True)
class AppliedSet:
    SetValue: SceneSet
    ApplyTypes: tuple[int, ...] | None
