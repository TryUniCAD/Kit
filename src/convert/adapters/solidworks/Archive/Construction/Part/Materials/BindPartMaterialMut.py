from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Part.Materials.MakePhysicalDensity import (
    MakePhysicalDensity,
)
from convert.adapters.solidworks.Archive.Construction.Part.Materials.PartMaterialInput import (
    PartMaterialInput,
)
from convert.adapters.solidworks.Archive.Construction.Presentation.MakeModelVisual import (
    MakeModelVisual,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# a fresh single configuration part needs separate physical and named owners before ordinary archive allocation
def BindPartMaterialMut(
    SystemValue: PartSystem, MaterialValue: PartMaterialInput
) -> None:
    RootValue = SystemValue.RootValue
    Configurations = SystemValue.ConfigValues
    if RootValue.ClassValue != RuntimeClass("moPart_c", 1) or len(Configurations) != 1:
        raise ValueError("part material requires one ordinary part configuration")
    ActiveValue = Configurations[0]
    ManagerFields = SystemValue.ManagerValue.FieldsValue
    if (
        ActiveValue.ClassValue != RuntimeClass("moPartConfiguration_c", 1)
        or ManagerFields.get("f360") is not ActiveValue
        or ManagerFields.get("f368") is not ActiveValue
    ):
        raise ValueError("part material requires the actual active configuration")
    RootFields, ConfigFields = RootValue.FieldsValue, ActiveValue.FieldsValue
    if (
        RootFields["f1420"] is not None
        or ConfigFields["fc50"] != -1.0
        or ConfigFields["f78"] is not None
    ):
        raise ValueError("part material requires fresh unassigned archive owners")
    DensityValue = float(MaterialValue.DensityValue)
    PhysicalValue = MakePhysicalDensity(DensityValue)
    VisualValue = MakeModelVisual()
    PropertiesValue = CastValue(dict[str, object], VisualValue.FieldsValue["f20"])
    PropertiesValue["f20"] = MaterialValue.IdentityValue
    RootFields["f1420"] = PhysicalValue
    ConfigFields["fc50"] = DensityValue
    ConfigFields["f78"] = VisualValue
