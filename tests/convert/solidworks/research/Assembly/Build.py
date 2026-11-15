from __future__ import annotations

from builtins import getattr as GetAttr
from types import ModuleType
from typing import cast as CastValue


# initial configuration ownership must originate from the same generated assembly used by archive references
def BuildRecords(
    InputData: dict[str, dict[str, object]],
    BuilderModule: ModuleType,
    ModelModule: ModuleType,
    CoreModule: ModuleType,
) -> tuple[object, object, dict[str, object]]:
    OwnerValue = GetAttr(CoreModule, "Obj")("moAssembly_c")
    ConfigValue = GetAttr(BuilderModule, "initial_configuration")(
        owner=OwnerValue, **InputData["configuration"]
    )
    ComponentValue = GetAttr(ModelModule, "unit_component")(owner=OwnerValue)
    FileValue = CastValue(
        dict[str, object],
        GetAttr(BuilderModule, "file_definition")(**InputData["file"]),
    )
    return ConfigValue, ComponentValue, FileValue
