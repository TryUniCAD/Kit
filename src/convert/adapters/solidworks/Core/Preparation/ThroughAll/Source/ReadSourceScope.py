from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireRecord
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.SourceOps import (
    SourceOps,
)
from interchange.document.Models.DocumentModel import CadDocument


# saved explicit body ownership must stay tied to the real stock producer rather than a generic all bodies fallback
def ReadSourceScope(DocumentValue: CadDocument, OwnersValue: SourceOps) -> str:
    Stock, CutValue = OwnersValue.StockValue, OwnersValue.CutValue
    if len(CutValue.selection_ids) != 1:
        raise ValueError("source cut requires one explicit stock selection")
    Choices = tuple(
        Value
        for Value in DocumentValue.selections
        if Value.id == CutValue.selection_ids[0]
    )
    if len(Choices) != 1 or len(Choices[0].path) != 1:
        raise ValueError("source selected stock path is missing or ambiguous")
    Choice = Choices[0]
    Element = Choice.path[0]
    if (
        (Element.entity_kind, Element.entity_id, Element.subelement)
        != ("feature", Stock.id, "body")
        or Choice.query
        or Choice.point is not None
        or Choice.attributes
    ):
        raise ValueError("source selection does not identify its actual stock producer")
    Evidence = RequireRecord(
        DocumentValue.metadata.get("solidworks.typed_resolved_semantics")
    )
    ScopeValue = RequireRecord(Evidence.get("cut_body_dependency"))
    if (
        ScopeValue.get("binding") != "saved_configuration_atom_alias"
        or ScopeValue.get("feature_scope_code") != 1
        or ScopeValue.get("producer_feature_id")
        != Stock.attributes.get("native_object_id")
        or ScopeValue.get("consumer_feature_id")
        != CutValue.attributes.get("native_object_id")
    ):
        raise ValueError("source body scope evidence is stale or unsupported")
    if DocumentValue.bodies[0].final_feature_id != CutValue.id:
        raise ValueError("source final body differs from its actual cut")
    return Choice.id
