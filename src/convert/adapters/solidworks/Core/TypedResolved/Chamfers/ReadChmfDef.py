from interchange.Features.FeatureKinds import ChamferFeature
from interchange.Records.RecordParameter import Parameter


# neutral mode and dimensions must retain the units and independent drives of their actual archive slots
def ReadChmfDef(ModeWord: int, Params: tuple[Parameter, ...]) -> ChamferFeature:
    Primary = Params[0].value
    if ModeWord == 1:
        return ChamferFeature(Primary, "distance_angle", angle=Params[1].value)
    if ModeWord == 2:
        return ChamferFeature(Primary, "two_distances", second_distance=Params[1].value)
    if ModeWord == 18:
        return ChamferFeature(Primary, "equal_distance")
    raise ValueError("cold chamfer has an unsupported portable dimension definition")
