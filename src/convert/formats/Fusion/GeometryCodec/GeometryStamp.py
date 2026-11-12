from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class GeometryStamp:
    Product: str
    Version: str
    SavedAt: str

    def __post_init__(Model) -> None:
        for Value in (Model.Product, Model.Version, Model.SavedAt):
            if not Value or not Value.isprintable():
                raise ValueError("Geometry provenance must be nonempty printable text")
            if len(Value.encode("utf-8")) > 255:
                raise ValueError("Geometry provenance exceeds its byte-count field")
