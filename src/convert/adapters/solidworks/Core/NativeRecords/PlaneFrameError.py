from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat


# inspection needs to distinguish a rejected stored datum from a missing reference
class PlaneFrameError(SldprtFormat):

    # the contradictory datum identifies the unresolved attachment without authorizing its use
    def __init__(self, PlaneId: int) -> None:
        super().__init__("SOLIDWORKS principal plane reference frame disagrees")
        self.PlaneId = PlaneId
