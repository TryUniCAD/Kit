from dataclasses import replace

from MakeAttachedAxes import make_axis_nodes, validate_axis_intents
from convert.adapters.solidworks.Archive.Construction.BodyNames.FinishNamedPart import FinishNamedPart
from convert.adapters.solidworks.Archive.Construction.BodyNames.NameOutputMut import NameOutputMut
from convert.adapters.solidworks.Archive.Construction.BodyNames.PlainBodyView import PlainBodyView
from convert.adapters.solidworks.Archive.Construction.BodyNames.ReadBodyKeys import ReadBodyKeys
from convert.adapters.solidworks.Archive.Construction.BodyNames.ReadBodyLabel import ReadBodyLabel
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import SetCfgStampMut
from convert.adapters.solidworks.Archive.Construction.Header.MakeRootLog import MakeRootLog
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartArchive import EmitPartArchive
from convert.adapters.solidworks.Archive.Construction.Part.FinishBlindMut import FinishBlindMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import MakePartHeaders
from convert.adapters.solidworks.Archive.Construction.Part.MakePartKeys import MakePartKeys
from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import MakePartProfMut
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import ProjectRectDims
from convert.adapters.solidworks.Archive.Construction.Patterns.Emission.MakePatKeys import PatKeyRow
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeCornerMut import MakeCornerMut
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeRectDimsMut import MakeRectDimsMut
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import MakeSketchKeys
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import RectDimInput
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, RequireNode
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.RequirePartPath import RequirePartPath


def make_stock(document, locator, creation, properties):
    plain = PlainBodyView(document)
    plan = ProjectRectDims(plain, TopAttached=True)
    if document.brep is not None or document.brep_payloads or document.units != "mm":
        raise ValueError("axis generation needs the clean signed authored stock only")
    output = RequirePartPath(locator, creation)
    recipe = MakePartRecipe(plan, creation)
    settings = replace(BindPartIntent(plain, plan, recipe, output), PropertiesValue=properties)
    CheckPartInput(plain, settings, plan)
    if plan.AxisValue != "y" or not plan.Reversed or plan.SecondDepth is not None:
        raise ValueError("only the signed reversed Top attached box has a proven stock recipe")
    allocator = PersistentIds()
    system = MakePartBaseMut(settings, plan, allocator)
    profile = MakePartProfMut(system, settings, plan, allocator)
    margin = min(plan.WidthValue, plan.HeightValue) / 4
    presentation = RectDimInput((plan.WidthValue / 2, margin), (-margin, -plan.HeightValue / 2), False, 1, False)
    dimensions = MakeRectDimsMut(profile, presentation, allocator, plan.SketchDriverNames)
    _ = MakeCornerMut(profile, system.OriginValue)
    candidate = FinishBlindMut(system, profile, settings, plan, allocator,
                               MakeSketchKeys(dimensions, settings.DocumentUnits.LengthUnit))
    label = ReadBodyLabel(document)
    if label != document.feature_timeline[0].name:
        _ = NameOutputMut(candidate, label)
    keys = ReadBodyKeys(document, plan, settings)
    return candidate, allocator, settings, keys


def make_axis_headers(system, settings, allocator, axes):
    SetCfgStampMut(system.ConfigValues[0], allocator)
    headers = MakePartHeaders(system, settings, allocator)
    for header in headers[:2]:
        log = RequireNode(header.FieldsValue["f20"], "suObList").FieldsValue
        if not isinstance(log["items"], tuple) or len(log["items"]) != 1:
            raise ValueError("the fresh axis construction requires its actual root creation row")
        for feature in axes:
            if (feature.FieldsValue.get("owner") is not system.RootValue
                    or allocator.Allocations.get((feature, "f08")) != FieldInt(feature.FieldsValue, "f08")):
                raise ValueError("axis creation record requires the actual allocated feature")
        log["items"] = (*log["items"], *(MakeRootLog(feature, settings.HeaderValue) for feature in axes))
    return headers


def make_part(document, locator, creation, properties, axes=None, *, origin_visible=True):
    if axes is not None:
        if origin_visible is not True:
            raise ValueError("the measured source profile supplies an enabled model origin")
        validate_axis_intents(axes, ())
    stock, allocator, settings, keys = make_stock(document, locator, creation, properties)
    if axes is None:
        return FinishNamedPart(stock, settings, keys)
    system = stock.SystemValue
    plan = stock.PlanValue
    roots = stock.ResolvedValue.RootsValue
    bounds = (0.0, -plan.DepthValue, 0.0), (plan.WidthValue, 0.0, plan.HeightValue)
    nodes = make_axis_nodes(system, settings, allocator, (stock.HeaderValue, stock.TopHeader),
                            bounds, axes, roots)
    headers = make_axis_headers(system, settings, allocator, nodes)
    keywords = MakePartKeys(system, roots, settings, plan, keys,
                            AdditionalRows=tuple(PatKeyRow(node) for node in nodes))
    streams, config, resolved = EmitPartArchive(system, (*roots, *nodes), headers, stock.DefinitionValue,
                                                settings, keywords)
    if any("Partition" in key or "LocalBodies" in key for key in streams):
        raise ValueError("an axis must not replace the cold stock with a cached kernel body")
    return replace(stock, HeaderValue=headers[0], TopHeader=headers[1], ManagerHeader=headers[2],
                   StreamsValue=streams, ConfigValue=config, ResolvedValue=resolved,
                   BytesValue=BuildSldprt(streams, FormatVersion=4))
