from dataclasses import dataclass, replace

from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakeSharedCopy import MakeSharedCopy
from convert.adapters.solidworks.Archive.Construction.BodyScope.BindStockMut import BindStockMut
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import SetCfgStampMut
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import DimensionGraph
from convert.adapters.solidworks.Archive.Construction.Files.MakeFileConfig import MakeFileConfig
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Header.MakeRootLog import MakeRootLog
from convert.adapters.solidworks.Archive.Construction.Model.MakeSelfComp import MakeSelfComp
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import MakePartHeaders
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import PartBuildInput
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import ProfileGraph
from convert.adapters.solidworks.Archive.Construction.Revolves.Feature.MakeRevFeatMut import MakeRevFeatMut
from convert.adapters.solidworks.Archive.Construction.Revolves.Sketch.MakeRevProfMut import MakeRevProfMut
from convert.adapters.solidworks.Archive.Construction.Sketch.RequirePolygon import RequirePolygon
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import PartSystem
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe

from StockCutGeometry import bbox_measure
from StockCutPlan import StockCutPlan, neutral_projection, require


@dataclass(frozen=True, slots=True)
class OperationOwners:
    profile: ProfileGraph
    feature: ArchiveNode
    end: ArchiveNode
    driver: DimensionGraph
    atom: ArchiveNode


@dataclass(frozen=True, slots=True)
class FaceNeighbours:
    own: ArchiveNode
    adjacent: frozenset[ArchiveNode]


@dataclass(frozen=True, slots=True)
class CutSurfaceOwners:
    stocks: tuple[tuple[FaceNeighbours, FaceNeighbours], tuple[FaceNeighbours, FaceNeighbours]]
    result: tuple[FaceNeighbours, FaceNeighbours]
    bounds: tuple[ArchiveNode, ArchiveNode, ArchiveNode]


@dataclass(frozen=True, slots=True)
class SelectedAtom:
    id: str
    feature: ArchiveNode
    atom: ArchiveNode
    local_component: ArchiveNode
    candidates: tuple[FaceNeighbours, FaceNeighbours]


@dataclass(frozen=True, slots=True)
class StockCutOwners:
    plan: StockCutPlan
    settings: PartBuildInput
    system: PartSystem
    headers: tuple[ArchiveNode, ArchiveNode, ArchiveNode]
    operations: tuple[OperationOwners, OperationOwners, OperationOwners]
    selector: SelectedAtom
    geometry: CutSurfaceOwners

    @property
    def roots(self):
        return (*self.system.FeatureValues,
                *(owner for value in self.operations for owner in (value.profile.ProfileValue, value.feature)))


def node(name, fields):
    return ArchiveNode(RuntimeClass(name, 1), fields)


def make_keeper(header, top, external, operation, mark, is_end=False):
    feature_id = operation.feature.FieldsValue["f08"]
    epoch = DatumTime(header, feature_id)
    require(epoch != 2592000 and DatumTime(top, feature_id) == epoch,
            "historical surface needs both actual feature creation logs")
    keeper = node("moFR_c", {"f08": external, "f10": {"f00": feature_id, "f08": epoch}})
    fields = {"f10": {"f08": None, "f10": keeper}, "f38": mark}
    if is_end:
        fields["f3c"] = 0
    return node("moEndFaceSurfIdRep_c" if is_end else "moFromSktEntSurfIdRep_c", fields)


def make_geometry(plan, system, headers, operations):
    header, top, _ = headers
    external = node("moExtObject_c", {
        **dict.fromkeys(("f48", "f4c", "f50", "f54", "f58", "f60", "f70", "f78"), 0),
        "refcfg": MakeFileConfig(system.RootValue, system.ConfigValues[0]),
        "shared": MakeSharedCopy(header.FieldsValue["f38"]),
    })

    def edge_rep(index, role):
        operation = operations[index]
        lines = RequirePolygon(operation.profile.GeometryValue).LineValues
        mark = lines[plan.sections[index].edges[role]].FieldsValue["f08"]
        return make_keeper(header, top, external, operation, mark)

    stocks = tuple(tuple(FaceNeighbours(edge_rep(index, wall), frozenset(
        edge_rep(index, role) for role in ("low", "high")
    )) for wall in ("inner", "outer")) for index in range(2))
    cut = operations[2]
    result = tuple(FaceNeighbours(
        make_keeper(header, top, external, cut, side, True),
        frozenset((edge_rep(plan.selected_index, plan.reached_wall),
                   *(edge_rep(2, role) for role in ("low", plan.result_wall, "high")))),
    ) for side in (0, 1))
    bounds = tuple(bbox_measure(plan.operations[0].AxisStart[0], operations[0].profile.FrameValue,
                                plan.sections[index]) for index in (0, 1, plan.selected_index))
    return CutSurfaceOwners(stocks, result, tuple(
        node("moBBoxCenterData_c", {"f08": 1, "f10": dict(zip("xyz", centre, strict=True)), "f28": diagonal})
        for centre, diagonal in bounds
    ))


def build_owners(document, locator, epoch):
    plan = neutral_projection(document)
    settings = replace(MakePartRecipe(plan.operations[0], epoch), OutputValue=SelfFileInput(locator, epoch))
    first, *others = plan.operations
    other_names = tuple(name for value in others for name in (value.SketchName, value.FeatureName))
    CheckPartInput(document, settings, first, other_names)
    allocator = PersistentIds()
    system = MakePartBaseMut(settings, first, allocator)
    manager = system.RootValue.FieldsValue["fd88"]
    operations = []
    for index, operation in enumerate(plan.operations):
        profile, axis = MakeRevProfMut(system, settings, operation, allocator)
        feature, _, end, driver = MakeRevFeatMut(system, profile, axis, settings, operation, allocator, IsCut=index == 2)
        feature.FieldsValue.update(f870=int(index != 1), f544=1)
        atom = BindStockMut(manager, feature, AppendMember=True)
        operations.append(OperationOwners(profile, feature, end, driver, atom))

    selected = operations[plan.selected_index]
    result = operations[2]
    selected.atom.FieldsValue["f144"] = 1
    result.feature.FieldsValue.update(has_f530=1, f530={"n": 1, "items": [{"o": selected.atom}]})
    SetCfgStampMut(system.ConfigValues[0], allocator)
    headers = MakePartHeaders(system, settings, allocator)
    for header in headers[:2]:
        logs = header.FieldsValue["f20"].FieldsValue
        logs["items"] = (*logs["items"], *(MakeRootLog(value.feature, settings.HeaderValue) for value in operations))

    first, second, cut = operations
    operations = (first, second, cut)
    geometry = make_geometry(plan, system, headers, operations)
    selector = SelectedAtom(plan.selection_id, selected.feature, selected.atom, MakeSelfComp(system.RootValue),
                            geometry.stocks[plan.selected_index])
    return StockCutOwners(plan, settings, system, headers, operations, selector, geometry)
