from typing import TypeAlias

from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndInput import (
    BlindEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Blind.BossEndInput import (
    BossEndInput,
)

# both caller domains share the native end object and five feature dimension lifetimes
KEndInput: TypeAlias = BlindEndInput | BossEndInput

# both native end constructors consume the model through this type
__all__ = ("KEndInput",)
