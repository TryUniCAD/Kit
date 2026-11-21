from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.CheckSourceEnv import (
    CheckSourceEnv,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ListSourceGaps import (
    ListSourceGaps,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ThruSourceEnv import (
    ThruSourceEnv,
)


# complete source admission must recompute missing field ownership rather than trust a caller edited or emptied envelope status
def RequireThruFull(EnvelopeValue: ThruSourceEnv) -> None:
    if type(EnvelopeValue) is not ThruSourceEnv:
        raise TypeError("complete source admission requires its actual source envelope")
    CheckSourceEnv(EnvelopeValue.DocumentValue)
    Missing = ListSourceGaps(EnvelopeValue.DocumentValue)
    if Missing or EnvelopeValue.UnmappedPaths:
        raise ValueError(
            "complete source construction has unrepresented fields: "
            + "; ".join(Missing or EnvelopeValue.UnmappedPaths)
        )
