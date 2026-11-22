from typing import Protocol


# all fresh part families need the same real neutral identity inputs before their distinct feature construction
class PartLabels(Protocol):

    # shared construction needs this actual neutral identity without depending on an unrelated feature plan
    @property
    def NameValue(self) -> str:
        raise NotImplementedError

    # shared construction needs this actual neutral identity without depending on an unrelated feature plan
    @property
    def ConfigName(self) -> str:
        raise NotImplementedError

    # shared construction needs this actual neutral identity without depending on an unrelated feature plan
    @property
    def PlaneName(self) -> str:
        raise NotImplementedError

    # shared construction needs this actual neutral identity without depending on an unrelated feature plan
    @property
    def AxisValue(self) -> str:
        raise NotImplementedError

    # shared construction needs this actual neutral identity without depending on an unrelated feature plan
    @property
    def SketchName(self) -> str:
        raise NotImplementedError

    # shared construction needs this actual neutral identity without depending on an unrelated feature plan
    @property
    def FeatureName(self) -> str:
        raise NotImplementedError
