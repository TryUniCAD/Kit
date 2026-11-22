from collections.abc import Mapping
from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Resolved.Sweeps.SwapSwBodyMut import KSwChoice


# the observed nonzero flag selects the existing field in its own serializer scope
def SwFlagChoice(NameValue: str) -> KSwChoice:
    return (
        "compare",
        ("NotEq",),
        ("lookup", ("scope",), ("literal", NameValue)),
        ("literal", 0),
    )


# saved body and profile references replace only the witnessed alternatives to their ordinary fields
KSwSavedChoices: Mapping[str, Mapping[KSwChoice, tuple[NativeField, ...]]] = (
    MappingProxyType(
        {
            "moAtomFeature_c": {
                SwFlagChoice("has_f528"): (
                    NativeField("Embed", "f528", "rf.suObArray"),
                ),
                "f498": (NativeField("Scalar", "v", "i32"),),
                SwFlagChoice("has_f4a8"): (
                    NativeField("Embed", "f4a8", "moBodyChooser_c"),
                ),
                SwFlagChoice("has_f4b0"): (
                    NativeField("Embed", "f4b0", "moBodyChooser_c"),
                ),
                SwFlagChoice("has_f4c0"): (
                    NativeField("Embed", "f4c0", "moBodyChooser_c"),
                ),
                SwFlagChoice("has_f3d0"): (
                    NativeField("Node", "f3d0", "moPMarkRecord_c"),
                    NativeField("Scalar", "f3c0", "i32"),
                    NativeField("Scalar", "f3c8", "i32"),
                    NativeField("Scalar", "f580", "i32"),
                ),
            },
            "moEndSpec_c": {
                SwFlagChoice("has_f28"): (NativeField("Embed", "f28", "rf.suObArray"),),
                SwFlagChoice("has_f48"): (NativeField("Embed", "f48", "rf.suObArray"),),
            },
            "moFeatureDim_c.FUN_4c833f00": {
                SwFlagChoice("has_ff0"): (
                    NativeField("Embed", "ff0", "mgXform_c.restore"),
                ),
                (
                    "BitAnd",
                    ("lookup_or", ("scope",), ("literal", "pt_flags"), ("literal", 0)),
                    ("literal", 2),
                ): (
                    NativeField("Embed", "fe0", "mgVector_c.restore"),
                    NativeField("Embed", "fe8", "mgVector_c.restore"),
                ),
            },
            "moProfileData.FUN_4bb2d5c0": {
                "f2a8": (NativeField("Node", "chain", "moSketchChain_c"),),
            },
        }
    )
)
