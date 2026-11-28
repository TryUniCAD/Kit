from collections.abc import Iterator

from convert.adapters.Fusion.Native.Graph.GraphValues import PointCoords
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode


# floats compare by representation so a camera zero sign remains observable
def CamFieldKeys(Camera: NativeNode) -> Iterator[tuple[str, object]]:
    for FieldName, Value in sorted(Camera.Fields.items()):
        if FieldName in ("position", "target", "up"):
            yield FieldName, tuple(
                Coordinate.hex() for Coordinate in PointCoords(Value)
            )
        elif isinstance(Value, float):
            yield FieldName, Value.hex()
        else:
            yield FieldName, Value
