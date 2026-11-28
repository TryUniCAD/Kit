from dataclasses import dataclass, replace
from math import tau

from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ProjectRevolve import ProjectRevolve
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import RevolvePlan
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.Features.FeatureBody import DesignBody
from interchange.geometry.Models.Selection import SelectPathElem
from interchange.Records.RecordTopology import TopologyCounts


@dataclass(frozen=True, slots=True)
class AnnularSection:
    radial: tuple[float, float]
    axial: tuple[float, float]
    edges: dict[str, int]


@dataclass(frozen=True, slots=True)
class StockCutPlan:
    operations: tuple[RevolvePlan, RevolvePlan, RevolvePlan]
    sections: tuple[AnnularSection, AnnularSection, AnnularSection]
    selection_id: str
    selected_index: int
    reached_wall: str
    result_wall: str
    radial_overlap: tuple[float, float]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def section(operation):
    vertices = operation.VerticesValue
    radial = tuple(sorted({x - operation.AxisStart[0] for x, _ in vertices}))
    axial = tuple(sorted({y for _, y in vertices}))
    inner, outer = radial
    low, high = axial
    axis = operation.AxisStart[0]
    edges = {}
    for index, (start, end) in enumerate(zip(vertices, (*vertices[1:], vertices[0]), strict=True)):
        if start[1] == end[1]:
            role = "low" if start[1] == low else "high"
        elif start[0] == end[0]:
            role = "inner" if start[0] - axis == inner else "outer"
        else:
            raise ValueError("rectangular operation has a diagonal contour edge")
        require(role not in edges, "rectangular operation repeats a surface role")
        edges[role] = index
    require(set(edges) == {"low", "high", "inner", "outer"} and inner > 0 and high > low,
            "rectangular operation has an invalid radial or axial extent")
    return AnnularSection((inner, outer), (low, high), edges)


def neutral_projection(document):
    require(type(document) is CadDocument, "selected revolve requires its actual neutral document")
    document.assert_valid()
    require(not (document.assembly or document.DrawingValue or document.brep or document.meshes
                 or document.brep_payloads or document.materials or document.diagnostics or document.capabilities
                 or document.source.attributes) and document.schema_version == "1.0",
            "selected revolve has an unrepresented neutral document owner")
    require(tuple(map(len, (document.configurations, document.support_planes, document.sketches, document.feature_timeline,
                            document.parameters, document.selections, document.bodies))) == (1, 1, 3, 3, 3, 4, 2),
            "selected revolve requires exactly two stocks, three D1s, and one explicit cut")
    stocks = document.feature_timeline[:2]
    cut = document.feature_timeline[2]
    features = (*stocks, cut)
    parameters = {value.id: value for value in document.parameters}
    selections = {value.id: value for value in document.selections}
    ordered = tuple(value.id for value in stocks)
    require(tuple(value.operation for value in features) == (BooleanOp.KCreate, BooleanOp.KCreate, BooleanOp.KCutOperation)
            and tuple(value.order for value in features) == (0, 1, 2)
            and all(not value.input_feature_ids for value in stocks)
            and len(cut.input_feature_ids) == 1 and cut.input_feature_ids[0] in ordered,
            "selected revolve requires two independent stocks and one actual prior producer dependency")
    chosen = ordered.index(cut.input_feature_ids[0])
    require(len(cut.selection_ids) == 2 and cut.selection_ids[1] in selections,
            "selected revolve requires a separate historical stock selection")
    body_pick = selections[cut.selection_ids[1]]
    require(body_pick.name == "Selected historical stock" and not body_pick.query and body_pick.point is None
            and body_pick.provenance is None and not body_pick.attributes
            and body_pick.path == (SelectPathElem("feature", ordered[chosen], "body"),),
            "selected stock reference differs from its actual historical producer")
    unchanged, result = document.bodies
    require((unchanged.final_feature_id, result.final_feature_id) == (ordered[1 - chosen], cut.id)
            and (unchanged.name, result.name) == (stocks[1 - chosen].name, cut.name)
            and all(value.topology == TopologyCounts() and value.provenance is None
                    and value.material_id is None and not value.attributes for value in document.bodies),
            "selected revolve must retain its ordered untouched and cut-result body owners")
    require(document.support_planes[0].provenance is None, "selected revolve support has source-only provenance")
    operations = []
    for feature, sketch in zip(features, document.sketches, strict=True):
        require(type(feature.definition) is AngularRevolve and feature.provenance is None
                and sketch.provenance is None
                and all(value.provenance is None for value in (*sketch.entities, *sketch.constraints)),
                "selected revolve operation has unrepresented feature or profile provenance")
        definition = feature.definition
        require(definition.SideMode == "one_sided" and feature.parameter_ids == (definition.AlongParameterId,)
                and definition.AlongParameterId in parameters and definition.AxisSelectionId in selections,
                "selected revolve requires its actual one-sided D1 and axis")
        parameter = parameters[definition.AlongParameterId]
        axis = selections[definition.AxisSelectionId]
        require(axis.name == "Selected local construction axis" and axis.provenance is None and parameter.provenance is None,
                "selected revolve axis or D1 has an unrepresented source owner")
        require(feature.selection_ids == ((axis.id, body_pick.id) if feature is cut else (axis.id,)),
                "selected revolve must own its actual ordered axis and body picks")
        body = result if feature is cut else unchanged
        body = body if feature is cut or feature.id == unchanged.final_feature_id else DesignBody(
            result.id, feature.name, feature.id,
        )
        geometry = replace(
            document,
            parameters=(parameter,), sketches=(sketch,), selections=(axis,), bodies=(body,),
            feature_timeline=(replace(feature, order=0, operation=BooleanOp.KCreate,
                                      input_feature_ids=(), selection_ids=(axis.id,)),),
        )
        operations.append(ProjectRevolve(geometry))
    first, second, tool = operations
    require(len({value.ParameterId for value in operations}) == len({value.SelectionId for value in operations}) == 3
            and len({value.AxisEntityId for value in operations}) == 3
            and {value.SelectionId for value in operations} | {body_pick.id} == set(selections)
            and {value.ParameterId for value in operations} == set(parameters),
            "selected revolve repeats or loses an actual driver or axis owner")
    require(all(value.AxisValue == first.AxisValue and value.AxisStart == first.AxisStart
                and value.AxisEnd == first.AxisEnd and value.EqualRule is None for value in operations)
            and not first.IsReverse and not second.IsReverse
            and first.AngleValue == second.AngleValue == tau and 0 < tool.AngleValue < tau,
            "selected revolve requires coaxial full stocks and a one-sided cut")
    sections = tuple(map(section, operations))
    inner, outer, tool_section = sections
    require(inner.radial[0] < tool_section.radial[0] < inner.radial[1] < outer.radial[0]
            < tool_section.radial[1] < outer.radial[1]
            and inner.axial == outer.axial
            and inner.axial[0] < tool_section.axial[0] < tool_section.axial[1] < inner.axial[1],
            "selected revolve requires disjoint stocks with a cutter crossing one interior wall of each")
    stock = sections[chosen]
    reached, remaining = ("outer", "inner") if stock is inner else ("inner", "outer")
    overlap = (max(stock.radial[0], tool_section.radial[0]), min(stock.radial[1], tool_section.radial[1]))
    return StockCutPlan((first, second, tool), sections, body_pick.id, chosen, reached, remaining, overlap)
