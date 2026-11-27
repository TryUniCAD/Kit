from dataclasses import replace as ReplaceValue

from interchange.document.Models.DocumentModel import CadDocument


# selected history corruptions preserve source scalars so validation must resolve the actual edge owner
def ChangeRimPick(Document: CadDocument, ModeName: str) -> CadDocument:
    Selected = Document.selections[0]
    Feature = Document.feature_timeline[-1]
    if ModeName == "vertex_query":
        return ReplaceValue(
            Document,
            selections=(
                ReplaceValue(Selected, path=(), query={"entity_kind": "vertex"}),
            ),
        )
    if ModeName == "wrong_curve":
        return ReplaceValue(
            Document,
            selections=(
                ReplaceValue(Selected, query=dict(Selected.query, curve_kind="line")),
            ),
        )
    if ModeName == "lower_query":
        return ReplaceValue(
            Document,
            selections=(
                ReplaceValue(
                    Selected, query=dict(Selected.query, position="lower_rim")
                ),
            ),
        )
    if ModeName == "missing_body":
        return ReplaceValue(
            Document,
            selections=(
                ReplaceValue(
                    Selected,
                    path=(
                        ReplaceValue(Selected.path[0], entity_id="missing-body"),
                        Selected.path[1],
                    ),
                ),
            ),
        )
    if ModeName == "foreign_body":
        Foreign = ReplaceValue(Document.bodies[0], id="foreign-body")
        return ReplaceValue(
            Document,
            bodies=(*Document.bodies, Foreign),
            selections=(
                ReplaceValue(
                    Selected,
                    path=(
                        ReplaceValue(Selected.path[0], entity_id=Foreign.id),
                        Selected.path[1],
                    ),
                ),
            ),
        )
    if ModeName in ("self_source", "missing_source"):
        SourceId = Feature.id if ModeName == "self_source" else "missing-source"
        Selected = ReplaceValue(
            Selected,
            path=(Selected.path[0], ReplaceValue(Selected.path[1], entity_id=SourceId)),
            query=dict(Selected.query, source_feature_id=SourceId),
        )
        Feature = ReplaceValue(Feature, input_feature_ids=(SourceId,))
        return ReplaceValue(
            Document,
            selections=(Selected,),
            feature_timeline=(*Document.feature_timeline[:-1], Feature),
        )
    if ModeName in ("missing_dependency", "extra_dependency"):
        Inputs = (
            ()
            if ModeName == "missing_dependency"
            else (*Feature.input_feature_ids, Document.feature_timeline[0].id)
        )
        return ReplaceValue(
            Document,
            feature_timeline=(
                *Document.feature_timeline[:-1],
                ReplaceValue(Feature, input_feature_ids=Inputs),
            ),
        )
    raise ValueError("Unknown neutral rim selection corruption")
