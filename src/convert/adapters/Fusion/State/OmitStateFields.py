from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismIds import PrismIds

# newly optional empty fields must not change established serialized document fingerprints
KStateOmit: dict[type[object], dict[str, object]] = {
    PrismHistory: {"Tracking": PrismIds()},
}
