from dataclasses import dataclass as Dataclass


# typed class boundaries must be shared without circular decoder imports
@Dataclass(frozen=True, slots=True)
class NativeClass:
    offset: int
    name: str
