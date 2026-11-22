from typing import Protocol

from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.StockCacheBody import (
    StockCacheBody,
)
from interchange.brep.Topology.BrepModel import BrepModel


# portable design construction needs joined body payload and geometry ownership across selected cut families
class BodyCacheView(Protocol):

    # only the proved active geometry may own the portable bodies
    @property
    def BrepValue(self) -> BrepModel:
        raise NotImplementedError

    # compare both physical bodies to their independent archive atoms
    @property
    def BodyValues(self) -> tuple[StockCacheBody, StockCacheBody]:
        raise NotImplementedError

    # attach both design bodies to their exact active partition
    @property
    def StreamName(self) -> str:
        raise NotImplementedError
