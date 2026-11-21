from dataclasses import dataclass as DataClass


# one generated view needs separate authored placement derived outlines and the two native sketch frames
@DataClass(frozen=True, slots=True)
class ViewProjection:
    FieldsValue: dict[str, object]
    HeaderBounds: dict[str, float]
    SheetFrame: dict[str, object]
    ModelFrame: dict[str, object]
    AxisValues: tuple[tuple[float, ...], ...]
