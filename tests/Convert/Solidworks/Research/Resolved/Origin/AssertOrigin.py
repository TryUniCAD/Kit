from math import isclose as IsClose

from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Solidworks.Research.Resolved.Origin.AssertOriginGeo import (
    AssertOriginGeo,
)
from tests.Convert.Solidworks.Research.Resolved.Origin.AssertOriRules import (
    AssertOriRules,
)


# actual public entities must retain four contour edges and one separate fixed construction datum with seven owned constraints
def AssertOrigin(
    DocumentValue: CadDocument, LengthValue: float, WidthValue: float
) -> None:
    (SketchValue,) = DocumentValue.sketches
    assert SketchValue.attributes["typed_line_loop"] is True
    assert SketchValue.attributes["typed_line_dimensions"] is True
    assert SketchValue.attributes["typed_origin_coincidence"] is True
    AssertOriginGeo(SketchValue, LengthValue, WidthValue)
    AssertOriRules(SketchValue)
    Parameters = {Param.id: Param for Param in DocumentValue.parameters}
    assert len(SketchValue.parameter_ids) == 2
    for ParameterId, Expected in zip(
        SketchValue.parameter_ids, (LengthValue, WidthValue), strict=True
    ):
        Parameter = Parameters[ParameterId]
        assert Parameter.value.unit == "mm"
        assert type(Parameter.value.value) is float
        assert IsClose(Parameter.value.value, Expected, rel_tol=1e-9, abs_tol=1e-9)
    DocumentValue.assert_valid()
