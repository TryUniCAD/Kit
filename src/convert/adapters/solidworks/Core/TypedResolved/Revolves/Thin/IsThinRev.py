from convert.adapters.solidworks.Core.Native import NativeModel


# the thin cold path is selected by its actual feature vocabulary before deriving any geometry
def IsThinRev(ModelValue: NativeModel) -> bool:
    return any(
        FeatureValue.class_name == "moRevolutionThin_c"
        or FeatureValue.kind == "Revolve-Thin"
        for FeatureValue in ModelValue.features
    )
