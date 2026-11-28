from convert.adapters.solidworks.Assembly.PlanarMates.PlanarContext import PlanarContext
from convert.adapters.solidworks.Core.TypedMates.PublicMateEnv import PublicMateEnv
from convert.adapters.solidworks.Core.TypedMates.ReadFixedFlags import ReadFixedFlags
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# the measured cylinder route must not widen to mixed children nested references or multiple configurations
def MakeCylContext(EnvValue: PublicMateEnv, LinkValue: NativeLink) -> PlanarContext:
    NativeValue = EnvValue.NativeValue
    ItemsValue = {Value.feature_id: Value for Value in NativeValue.occurrences}
    Definitions = {Value.object_id: Value for Value in NativeValue.definitions}
    if (
        len(ItemsValue) != 2
        or len(NativeValue.occurrences) != 2
        or len(Definitions) != 2
        or len(NativeValue.definitions) != 2
        or len({Value.definition_id for Value in ItemsValue.values()}) != 1
        or any(Value.configuration_id != 0 for Value in ItemsValue.values())
        or len({Value.configuration_name for Value in ItemsValue.values()}) != 1
    ):
        raise ValueError(
            "concentric scope requires two direct occurrences of one actual child configuration"
        )
    Context = PlanarContext(
        LinkValue.ConfigValue.RootValue, ItemsValue, Definitions, {}
    )
    if sum(Value["fixed"] is True for Value in ReadFixedFlags(Context)) != 1:
        raise ValueError("concentric scope requires one actual fixed occurrence")
    return Context
