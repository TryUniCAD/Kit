from struct import pack

from ColdFilletAnno import bind_annotations
from ColdFilletIntent import FEATURE_NAME
from FilletModel import require

from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfEdgeRoles import PickChmfRoles
from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfRefOwners import (
    MakeChmfCarrier, MakeChmfFile, MakeChmfNode, ReadChmfOwner,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfStockGeom import MakeChmfStock
from convert.adapters.solidworks.Archive.Construction.Chamfers.MakeChmfGraph import BindChmfAtomMut, LogChmfMut
from convert.adapters.solidworks.Archive.Construction.Chamfers.MakeChmfRefs import MakeChmfEdge
from convert.adapters.solidworks.Archive.Construction.Circles.MakeRadialTail import MakeRadialTail
from convert.adapters.solidworks.Archive.Construction.Circles.ReadRadialStyle import ReadRadialStyle
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import DimensionGraph
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeCommonView import MakeViewForOwn
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeHandleMut import MakeHandleMut
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeLengthParam import MakeLengthParam
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeObList import MakeObList
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeValueFields import MakeValueFields
from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import KAtomLists, KAtomWords
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import InitFeatureMut
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.CheckViewArgs import CheckViewArgs
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName


def initial_feature(model, settings):
    feature = MakeChmfNode("Fillet_c", {})
    InitFeatureMut(feature, FEATURE_NAME, model, settings.TargetValue)
    fields = feature.FieldsValue
    fields.update(dict.fromkeys(KAtomWords, 0))
    fields.update({name: [] for name in KAtomLists})
    fields.update(dict.fromkeys(("f6e0", "f758", "f878", "f880", "f830", "f888", "f8b8",
                                 "f838", "f840", "fc40"), None))
    fields.update({name: MakeObList() for name in ("f368", "f388", "f780", "f8f8", "f9e8", "fc20")})
    fields.update({name: MakeChmfNode("suObList", MakeObList()) for name in ("f850", "f858", "f860", "f870")})
    fields.update({name: [] for name in ("f890", "f9b8", "fa60", "fbf0")})
    fields.update(
        f820={"f18": MakeObList(), "ff0": MakeObList()},
        f828={"f18": MakeObList(), "fe0": MakeObList()},
        f35c=0, f4a0=1, f7a0=0, has_f8e0=0, f808=1, f81c=0, f8e8=0,
        f930=0, f8d4=2, f8d8=2, f8dc=1, f940=0, f934=0, f918=0,
        f920=0.5, f928=0.5, f93c=1, f944=0, f948=0, has_f810=0,
        has_f734=1, f734=0, n890=0, n9b8=0, na60=0, fb00=0, f8c8=-1,
        f8cc=-1, f8d0=0, fb98=0, nbf0=0, f94c=0, f8ec=0, f8f0=0, fc48=0,
    )
    return feature


def make_driver(model, feature, radius):
    parameter = MakeLengthParam(feature, radius)
    dimension = MakeChmfNode("ThreeDRadiusDim_c", MakeValueFields(feature, parameter))
    handle = MakeHandleMut(feature, dimension)
    require(feature.ClassValue == RuntimeClass("Fillet_c", 1) and FieldInt(feature.FieldsValue, "f2b0") == 19000
            and parameter.ClassValue == RuntimeClass("moLengthParameter_c", 1) and ReadNodeName(parameter) == "D1"
            and handle.FieldsValue["owner"] is dimension.FieldsValue["owner"] is feature
            and handle.FieldsValue["ff0"] is dimension and dimension.FieldsValue["f28"] is parameter,
            "cold fillet radial display requires its own ordinary native dimension and parameter")
    CheckViewArgs(True, 0)
    fields = MakeViewForOwn(feature, handle, True, 0, 20)
    style, solid = ReadRadialStyle(model, False)
    require(solid, "cold solid edge requires ordinary solid radial line styling")
    fields.update(style.ProjectionValue)
    fields.update(MakeRadialTail(False, solid))
    fields.update(f950=radius, f7f8="R", f3e0=fields["f3e0"] & ~0x200,
                  f8a4=(fields["f8a4"] & ~0x8050) | style.UnderText,
                  fb64=(fields["fb64"] & ~0x103000) | style.FlagValue | 0x800,
                  fb60=fields["fb60"] | 0x200)
    fields["f5b0"]["data"] = pack("<d", radius)
    return DimensionGraph(parameter, dimension, handle, MakeChmfNode("moDisplayRadialDim_c", fields))


def bind_selection(stock, feature, atom, driver, roles):
    selected_owner = ReadChmfOwner(stock, stock.BossValue.FeatureValue)
    self_file = MakeChmfFile(stock)
    carriers = tuple(MakeChmfCarrier(role, selected_owner, self_file) for role in roles)
    model = stock.SystemValue.RootValue
    selected, reference = MakeChmfEdge(carriers, FieldInt(atom.FieldsValue, "f140"), model)
    selected.FieldsValue["f1c"] = 0
    radial_fields = {**selected.FieldsValue, "f18": 0, "f1c": 0, "fe8": reference}
    radial = MakeChmfNode("moCompEdge_c", radial_fields)
    item = MakeChmfNode("edgeRadiusObject_c", {"f08": driver.DisplayValue, "f10": radial, "f20": 0})
    feature.FieldsValue["f848"] = MakeChmfNode("suObList", MakeObList(selected))
    feature.FieldsValue["f868"] = MakeChmfNode("suObList", MakeObList(item))


def make_fillet(stock, intent, settings):
    model = stock.SystemValue.RootValue
    feature_id = FieldInt(stock.HeaderValue.FieldsValue, "f08")
    require(feature_id == FieldInt(stock.TopHeader.FieldsValue, "f08")
            and stock.ResolvedValue.RootsValue[-1] is stock.BossValue.FeatureValue,
            "cold fillet must extend the current stock and header allocator")
    roles = PickChmfRoles(MakeChmfStock(stock), intent.edge)
    allocator = PersistentIds(feature_id)
    feature = initial_feature(model, settings)
    driver = make_driver(model, feature, intent.definition.Radius.value)
    bind_annotations(model, driver.DisplayValue, settings.TargetValue.FileVersion, intent.annotations)
    allocator.AllocateMut(driver.DimensionValue, "f50")
    allocator.AllocateMut(feature)
    atom = BindChmfAtomMut(stock, feature)
    LogChmfMut(stock, feature, settings, allocator)
    bind_selection(stock, feature, atom, driver, roles)
    stock.SystemValue.ManagerValue.FieldsValue["f658"] = 1
    return feature, driver
