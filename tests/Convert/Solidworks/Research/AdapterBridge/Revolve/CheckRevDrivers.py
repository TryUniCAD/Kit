from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureAngleRev import AngularRevolve


# strict readback must preserve the actual angular drivers and their feature owner
def CheckRevDrivers(Parsed: CadDocument, ModeValue: str, TwoSides: bool) -> None:
    (Feature,) = (
        FeatureValue
        for FeatureValue in Parsed.feature_timeline
        if isinstance(FeatureValue.definition, AngularRevolve)
    )
    Definition = Feature.definition
    assert isinstance(Definition, AngularRevolve)
    assert Definition.SideMode == ModeValue
    Drivers = {Driver.id: Driver for Driver in Parsed.parameters}
    Along = Drivers[Definition.AlongParameterId]
    assert Along.name == "D1" and Along.value.value == 1.25
    assert Along.owner_id == Feature.id
    Against = Definition.AgainstParameterId
    if TwoSides:
        assert Against is not None and Against != Along.id
        assert Drivers[Against].name == "D2" and Drivers[Against].value.value == 0.875
        assert Drivers[Against].owner_id == Feature.id
    else:
        assert Against is None
