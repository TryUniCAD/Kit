from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Core.Native import NativeModel

# the legacy diagnostic identifies candidates without admitting their ownership
KLegacyStop = "multiple operation histories are outside typed blind topology"


# both stock routes retain the existing read options and ordinary history boundary
def IsStockModel(Model: NativeModel, Settings: ReadOptions) -> bool:
    return (
        Settings.include_brep
        and not Settings.extract_raw_brep
        and Model.active_configuration_id == 0
        and not Model.equations
        and Model.TypedGraph.get("diagnostic") == KLegacyStop
        and tuple(
            (Value.configuration_id, Value.name) for Value in Model.configurations
        )
        == ((0, "Default"),)
        and tuple(Value.kind for Value in Model.operations) == ("join", "join", "cut")
    )
