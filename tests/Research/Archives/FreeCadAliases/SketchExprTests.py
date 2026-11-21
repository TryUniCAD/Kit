from pathlib import Path as FilePath

from pytest import mark as MarkValue, raises as Raises

from convert import write_document as WriteDocument
from convert.adapters.registry.RegistryErrors import NotFoundError
from tests.Research.Archives.FreeCadAliases.ReadPadCase import ReadPadCase


# exact source ownership and the saved length must agree before the dependency is exposed
@MarkValue.parametrize(
    "CaseName",
    ("native", "stale", "label", "duplicate", "subelement", "inactive", "reference"),
)
def CheckPadExpr(TmpPath: FilePath, CaseName: str) -> None:
    Document = ReadPadCase(TmpPath, CaseName)
    (SketchValue,) = Document.sketches
    (Feature,) = Document.feature_timeline
    assert not SketchValue.suppressed
    (DepthValue,) = (
        Value for Value in Document.parameters if Value.owner_id == Feature.id
    )
    assert DepthValue.id == "freecad:parameter:Boss:Length"
    assert DepthValue.value.value == (17.0 if CaseName == "stale" else 16.0)
    assert DepthValue.value.unit == "mm"
    assert DepthValue.expression is not None
    ObjectName = "Caption" if CaseName == "label" else "Layout"
    assert DepthValue.expression.source == f"{ObjectName}.Constraints.span / 3"
    if CaseName == "native":
        (RuleValue,) = SketchValue.constraints
        ParamId = "freecad:parameter:Layout:constraint:0"
        assert RuleValue.parameter_id == ParamId
        assert DepthValue.expression.parameter_ids == (ParamId,)
    else:
        assert not DepthValue.expression.parameter_ids
        assert any(
            Finding.code == "freecad.sheet_alias.unresolved"
            for Finding in Document.diagnostics
        )
    if CaseName in {"inactive", "reference"}:
        (RuleValue,) = SketchValue.constraints
        assert RuleValue.suppressed is (CaseName == "inactive")
        assert RuleValue.driving is (CaseName != "reference")
    if CaseName == "stale":
        Target = TmpPath / "refused" / "Unsupported.SLDPRT"
        with Raises(NotFoundError):
            _ = WriteDocument(
                Document,
                Target,
                destination_format="solidworks.sldprt",
                allow_carrier=False,
                values={"require_native_transfers": True},
            )
        assert not Target.parent.exists()
