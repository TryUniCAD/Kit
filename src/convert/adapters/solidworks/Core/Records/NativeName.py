from dataclasses import dataclass as Dataclass


# native owner labels must remain reusable without loading the complete decoder
@Dataclass(frozen=True, slots=True)
class NativeName:
    offset: int
    text_end: int
    name: str
    object_id: int | None
    class_token: int
