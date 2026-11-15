from __future__ import annotations

from interchange.geometry.models.Transform import Transform


def IsIdentity(Value: Transform) -> bool:
    return (
        (Value.origin.x, Value.origin.y, Value.origin.z) == (0.0, 0.0, 0.0)
        and (Value.x_axis.x, Value.x_axis.y, Value.x_axis.z) == (1.0, 0.0, 0.0)
        and (Value.y_axis.x, Value.y_axis.y, Value.y_axis.z) == (0.0, 1.0, 0.0)
        and (Value.z_axis.x, Value.z_axis.y, Value.z_axis.z) == (0.0, 0.0, 1.0)
    )
