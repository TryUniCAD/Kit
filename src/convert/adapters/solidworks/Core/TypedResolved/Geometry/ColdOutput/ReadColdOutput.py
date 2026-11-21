from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ColdOutput import (
    ColdOutput,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.CheckColdAtom import (
    CheckColdAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.FindColdAtom import (
    FindColdAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ReadColdBoss import (
    ReadColdBoss,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName


# the new route admits only witnessed authored output ownership without relaxing the empty manager path
def ReadColdOutput(LinkValue: NativeLink) -> ColdOutput | None:
    AtomValue = FindColdAtom(LinkValue)
    if AtomValue is None:
        return None
    CheckColdAtom(AtomValue)
    BossValue = ReadColdBoss(LinkValue, AtomValue)
    NameValue = ReadNativeName(AtomValue)
    if (
        not 1 <= len(NameValue) <= 255
        or not NameValue.isascii()
        or not NameValue.isprintable()
    ):
        raise ValueError(
            "cold output name is outside the native-qualified ASCII profile"
        )
    return ColdOutput(LinkValue, AtomValue, BossValue, NameValue)
