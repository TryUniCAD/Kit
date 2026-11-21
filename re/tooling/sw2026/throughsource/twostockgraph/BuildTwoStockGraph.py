from dataclasses import dataclass, replace

from convert.adapters.solidworks.Archive.Construction.Blind.BossEndInput import (
    BossEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Blind.MakeEndSpec import (
    MakeEndSpec,
)
from convert.adapters.solidworks.Archive.Construction.BodyScope.MakeBodyRef import (
    MakeBodyRef,
)
from convert.adapters.solidworks.Archive.Construction.BodyScope.MakeStockAtom import (
    MakeStockAtom,
)
from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import (
    CircleInput,
)
from convert.adapters.solidworks.Archive.Construction.Circles.MakeCircleFeat import (
    MakeCircleFeat,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import (
    SetCfgStampMut,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.BindExtrusionMut import (
    BindExtrudeMut,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.CutGraph import CutGraph
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeExtrusionDimMut import (
    MakeEndDimMut,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeExtrusionNodeMut import (
    MakeExtrudeMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import (
    MakePartBaseMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.MakeThruCutMut import (
    MakeThruCutMut,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.MakeThruProfile import (
    MakeThruProfile,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughEndInput import (
    ThroughEndInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughStock import (
    ThroughStock,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from interchange.document.Models.DocumentModel import CadDocument

from BuildTwoStockShape import TwoStockShape, build_two_stock_shape
from ShapeIntent import project_intent, require, xyz


@dataclass(frozen=True)
class BlindStock:
    plan: ThroughStock
    profile: ProfileGraph
    feature: ArchiveNode
    end: ArchiveNode
    driver: DimensionGraph
    atom: ArchiveNode


@dataclass(frozen=True)
class OwnerGraph:
    document: CadDocument
    shape: TwoStockShape
    selected: BlindStock
    system: PartSystem
    settings: PartBuildInput
    allocator: PersistentIds
    stocks: tuple[BlindStock, BlindStock]
    cut: CutGraph
    selection: ArchiveNode
    ordered_roots: tuple[ArchiveNode, ...]


def native_axes(frame):
    basis = tuple(
        xyz(value) for value in (frame.origin, frame.x_axis, frame.y_axis, frame.z_axis)
    )
    for name in ("z", "x"):
        native = PrincipalFrame(name)
        if basis == (
            native.OriginValue,
            native.AxisU,
            native.AxisV,
            native.NormalValue,
        ):
            return name
    raise ValueError(
        "two stock archive graph requires canonical positive Front and Right supports"
    )


def stock_plan(document, stock, name, feature, sketch, plane, body_id):
    require(
        stock.extent[0] == 0,
        "two stock archive graph requires forward blind stock ends",
    )
    points = tuple((point.x * 0.001, point.y * 0.001) for point in stock.corners)
    return ThroughStock(
        name,
        document.configurations[0].name,
        plane.name,
        sketch.id,
        sketch.name,
        feature.id,
        feature.name,
        stock.driver_id,
        body_id,
        points,
        stock.extent[1] * 0.001,
        points[2][0] - points[0][0],
        points[2][1] - points[0][1],
        native_axes(stock.frame),
    )


def bind_stock_atom(feature, atom_id):
    atom = MakeStockAtom(feature, atom_id)
    feature.FieldsValue.update(
        has_f528=1,
        f528={"n": 1, "items": [{"o": atom}]},
        n494=1,
        f498=[{"v": atom_id}],
    )
    return atom


def make_stock(system, settings, plan, allocator, mode, atom_id):
    profile = MakeThruProfile(system, settings, plan, allocator)
    feature = MakeExtrudeMut(
        "moExtrusion_c" if mode == -1 else "moICE_c",
        plan.FeatureName,
        system.RootValue,
        settings.TargetValue,
        allocator,
    )
    input_end = BossEndInput(
        plan.DepthValue, False, settings.TargetValue.FileVersion, "blind"
    )
    driver = MakeEndDimMut(
        feature, input_end, 1, settings.DesignIntent, settings.SelectedLeader, allocator
    )
    end = MakeEndSpec(
        "blind",
        False,
        driver.DisplayValue,
        None,
        None,
        None,
        ArchiveNode(RuntimeClass("moFromEndSpec_c", 1), {"t": 0}),
    )
    flags = FieldInt(feature.FieldsValue, "f28")
    BindExtrudeMut(feature, profile, end)
    feature.FieldsValue.update(f28=flags | 0x140, f810=mode)
    return BlindStock(
        plan, profile, feature, end, driver, bind_stock_atom(feature, atom_id)
    )


def build_owner_graph(document, written_at):
    intent = project_intent(document)
    name = document.metadata.get("name")
    require(
        type(name) is str and bool(name.strip()),
        "owner graph requires an actual authored document name",
    )
    features = {feature.id: feature for feature in document.feature_timeline}
    require(
        all(
            body.name == features[body.final_feature_id].name
            for body in document.bodies
        ),
        "two stock owner graph requires implicit feature-derived body names",
    )
    models = {
        intent.selected.feature_id: intent.selected,
        intent.untouched.feature_id: intent.untouched,
    }
    planes = {plane.id: plane for plane in document.support_planes}
    sketches = {sketch.id: sketch for sketch in document.sketches}
    names = tuple(
        owner.name
        for owner in (*features.values(), *sketches.values(), *planes.values())
    )
    require(
        all(label.strip() for label in names) and len(set(names)) == len(names),
        "two stock archive graph requires distinct authored owner names",
    )
    body_ids = {body.final_feature_id: body.id for body in document.bodies}
    body_ids[intent.selected.feature_id] = (
        f"{intent.selected.feature_id}:historical-stock"
    )
    plans = tuple(
        stock_plan(
            document,
            model,
            name,
            feature,
            sketches[feature.sketch_id],
            planes[model.support_id],
            body_ids[feature.id],
        )
        for feature in document.feature_timeline[:2]
        for model in (models[feature.id],)
    )
    require(
        tuple(plan.AxisValue for plan in plans) == ("z", "x"),
        "two stock archive graph requires Front then Right stock support order",
    )
    shape = build_two_stock_shape(document)
    by_identity = {plan.FeatureId: plan for plan in plans}
    selected = by_identity[intent.selected.feature_id]
    cut = features[intent.cut_id]
    recipe = MakePartRecipe(selected, written_at)
    settings = BindPartIntent(document, selected, recipe, recipe.OutputValue)
    plane_names = {plan.AxisValue: plan.PlaneName for plan in plans}
    settings = replace(
        settings,
        SystemValue=replace(
            settings.SystemValue,
            PlaneNames=tuple(
                (axis, plane_names.get(axis, label))
                for axis, label in settings.SystemValue.PlaneNames
            ),
        ),
    )
    allocator = PersistentIds()
    system = MakePartBaseMut(settings, selected, allocator)
    part = system.RootValue
    manager = part.FieldsValue["fd88"]
    require(
        isinstance(manager, dict)
        and manager["n6c"] == 0
        and not manager["atoms"]
        and manager["fa8"] == 0,
        "two stock graph requires its fresh root atom manager",
    )
    start_id = FieldInt(manager, "f260")
    stocks = tuple(
        make_stock(system, settings, plan, allocator, mode, start_id + offset)
        for offset, (mode, plan) in enumerate(zip((-1, 0), plans, strict=True), 1)
    )
    manager.update(
        f260=start_id + len(stocks),
        n6c=len(stocks),
        atoms=[{"o": stock.atom} for stock in stocks],
    )
    (selected_stock,) = (stock for stock in stocks if stock.plan is selected)
    circle = intent.circle
    version = settings.TargetValue.FileVersion
    cut_profile = MakeCircleFeat(
        sketches[cut.sketch_id].name,
        part,
        system.SystemValues.PlaneValues[selected.AxisValue],
        selected.AxisValue,
        CircleInput(
            (circle.center.x * 0.001, circle.center.y * 0.001),
            circle.radius * 0.001,
            version,
        ),
        settings.TargetValue,
        allocator,
    )
    cutter = MakeThruCutMut(
        cut.name,
        part,
        cut_profile,
        ThroughEndInput("through_all", True, version),
        settings.TargetValue,
        allocator,
    )
    selector = MakeBodyRef(part, selected_stock.feature, selected_stock.atom)
    cutter.FeatureValue.FieldsValue.update(
        f544=1, has_f548=1, f548={"n": 1, "items": [{"o": selector}]}
    )
    SetCfgStampMut(system.ConfigValues[0], allocator)
    roots = (
        *system.FeatureValues,
        *(
            node
            for stock in stocks
            for node in (stock.profile.ProfileValue, stock.feature)
        ),
        cutter.ProfileValue.ProfileValue,
        cutter.FeatureValue,
    )
    return OwnerGraph(
        document,
        shape,
        selected_stock,
        system,
        settings,
        allocator,
        stocks,
        cutter,
        selector,
        roots,
    )
