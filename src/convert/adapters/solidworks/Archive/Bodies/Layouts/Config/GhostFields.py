from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# ordinary empty ghost managers retain the same row ownership as the populated layout
KGhostFields = MappingProxyType(
    {
        "moGhostBodyIdManager_c.FUN_4bf050e0": (
            NativeField("Scalar", "f80", "i32"),
            NativeField("GhostCount", "n", OtherName="fe0", CountValue="objects"),
            NativeField(
                "Repeat",
                "objects",
                BodyValue=(
                    NativeField("Embed", "o", "moGhostBodyObject_c.FUN_4bf05390"),
                ),
                CountValue="n",
                ModeValue="Positive",
            ),
        )
    }
)
