from dataclasses import dataclass as Dataclass


# profile recognition depends on marker identities and their original stream positions
@Dataclass(frozen=True, slots=True)
class NativeMarker:
    offset: int
    length: int
    prefix: str
    native_kind: int
    locus: str
    profile_role: int
    state: float | None
    object_index: int | None
    local_id: int | None
    coordinates_mm: tuple[float, float] | None
    endpoint_indices: tuple[int, int] | None
    construction: bool
    semantic: str
    data: bytes = b""
    coordinates_metres: tuple[float, float] | None = None
