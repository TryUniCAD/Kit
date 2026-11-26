from dataclasses import dataclass


# configured catalogue shortcuts need a validated contract before they can select a checkout
@dataclass(frozen=True)
class RunPreset:
    RootPath: str
    OutputRoot: str
    Options: dict[str, str | bool]
