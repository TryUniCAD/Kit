from pytest import approx as NearValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureDistExt import DistanceExtrude


# driving relationships must survive native reconstruction instead of only retaining an unbound numeric height
def VerifyDrive(Document: CadDocument, ExpectedHeight: float) -> None:
    assert not Document.diagnostics and not Document.brep_payloads
    assert len(Document.feature_timeline) == 2
    Definition = Document.feature_timeline[-1].definition
    assert isinstance(Definition, DistanceExtrude)
    Parameters = {Parameter.id: Parameter for Parameter in Document.parameters}
    Distance = Parameters[Definition.AlongParameterId]
    assert Distance.value.unit == "mm"
    assert Distance.value.value == NearValue(ExpectedHeight)
    assert Distance.expression is not None
    assert len(Distance.expression.parameter_ids) == 1
    Driver = Parameters[Distance.expression.parameter_ids[0]]
    assert Driver.name == "kitHeight"
    assert Driver.value.value == NearValue(ExpectedHeight)
