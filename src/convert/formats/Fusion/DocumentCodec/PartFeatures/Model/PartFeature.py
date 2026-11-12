from typing import TypeAlias

from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import ShellSpec

KPartFeature: TypeAlias = FilletSpec | ChamferSpec | ShellSpec
