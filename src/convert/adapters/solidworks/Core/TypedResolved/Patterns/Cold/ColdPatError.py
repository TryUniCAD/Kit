from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat


# strict reads need the same history refusal before and after neutral pattern projection
class ColdPatError(SldprtFormat):

    # the public refusal retains the actual failed typed owner as its cause
    def __init__(self) -> None:
        super().__init__(
            "cache-free linear pattern lacks a verified typed feature history"
        )
