from dataclasses import asdict
from pathlib import PureWindowsPath

from PlanarRegistryBuild import require
from PlanarVisualOwners import DISPLAY, PROPERTY, STATE, key_data, node
from para.concentric.AuditConcentricDisplayState import attrs_for
from para.concentric.ProveVisualStateStore import replay
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.BasicPbrInput import BasicPbrInput
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.ClassicLook import ClassicLook
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.MakeRenderLook import MakeRenderLook
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.PartLookInput import PartLookInput
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.PlanLookIds import PlanLookIds
from convert.adapters.solidworks.Archive.Definition.EmptyManagers.ReadEmptyMgrs import ReadEmptyMgrs
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


RESOURCE = r"graphics\materials\color.p2m"


def from_json(data):
    require(type(data) is dict and set(data) == set(PartLookInput.__dataclass_fields__),
            "renderer request lacks its exact neutral model fields")
    classic, shader = (data[key] for key in ("ClassicValue", "ShaderValue"))
    require(type(classic) is dict and set(classic) == set(ClassicLook.__dataclass_fields__)
            and type(shader) is dict and set(shader) == set(BasicPbrInput.__dataclass_fields__),
            "render request lacks its actual classic and DSPBR inputs")
    color_fields = ("AlbedoRgb", "AttenuationRgb", "SheenRgb")
    return PartLookInput(**{**data, "MainRgb": tuple(data["MainRgb"]), "HiddenLineRgb": tuple(data["HiddenLineRgb"]),
        "ClassicValue": ClassicLook(**classic), "ShaderValue": BasicPbrInput(**{
            **shader, **{key: tuple(shader[key]) for key in color_fields}})})


def rgb(value):
    require(type(value) is int and 0 <= value <= 0xFFFFFF,
            "renderer source packed color lies outside the unsigned RGB profile")
    return tuple((value >> shift) & 255 for shift in (0, 8, 16))


def shader_rgb(fields, stem):
    return tuple(round(fields[f"{stem}_{index}"] * 255) for index in range(3))


def material_id(visual):
    value = visual["f20"]["f90"]
    low, high = value["f00"], value["f04"]
    require(type(low) is int and type(high) is int and all(0 <= word <= 0xFFFFFFFF for word in (low, high)),
            "renderer source uses invalid unsigned ID halves")
    return low | (high << 32)


def carries_render(value):
    fields = node(value, "moVisualProperties_c")
    material = fields["f20"]
    require(fields.get("has88") == material.get("has90") == 1
            and type(fields.get("f88")) is dict and type(material.get("f90")) is dict,
            "renderer source lacks its classic and DSPBR owners")
    return fields


def observe_looks(archive, reg, *, generated=False):
    link = ReadNativeLink(archive, 0)
    root = link.ConfigValue.RootValue
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000).RootValue.FieldsValue
    config = manager["f360"]
    selected, = manager["f370"]["items"]
    require(root.ClassValue.NameValue == "moPart_c" and config.ClassValue.NameValue == "moPartConfiguration_c"
            and config is manager["f368"] is selected["o"] and manager["f370"]["n"] == 1
            and config.FieldsValue["f08"] == 0 and ReadNodeName(config) == "Default",
            "renderer requires the actual ordinary linked part and selected configuration")
    model_material = root.FieldsValue["f1420"]
    if generated:
        require(model_material is None, "renderer-only construction changed the independent physical material owner")
        density = None
    else:
        physical = node(node(model_material, "moMaterial_c")["f08"], "moDensityParameter_c")
        density = [physical["f58"], physical["f68"]]
        require(density == [1000.0, 0], "renderer source requires the observed unassigned density parameter")
    require(config.FieldsValue["fc50"] == -1.0
            and not config.FieldsValue["f420"] and not config.FieldsValue["f430"]
            and config.FieldsValue["fcb8"] is None
            and not config.FieldsValue["f600"].get("n", 0),
            "renderer source requires no assigned atom or configuration material")
    definition_data = archive.require("Contents/Definition")
    definition = ReadModelDef(definition_data, 19000).GraphValue
    managers = ReadEmptyMgrs(definition)
    require(managers.AppearanceValue.ManagerOnWire
            and WriteModelDef(definition).OutputValue == definition_data,
            "renderer requires the exact independent empty Definition manager owner")
    store, summary = replay(archive, reg)
    visual = key_data(store, config.FieldsValue["f08"], DISPLAY)
    require(visual["n_comps"] == 0 and visual["n_ents"] == 6,
            "renderer source needs the actual six-row part self display state")
    holder, *_ = visual["f78"]
    holder_ref = node(holder["ref"], "moCompHolder_c")
    require(node(holder_ref["f58"], "moUnitComponent_c") == {"owner": None, "has_ext": 0},
            "renderer source holder is not the detached part self owner")
    properties, _ = attrs_for(holder["attrs"], holder["m"], 1, (PROPERTY, STATE))
    roles = root.FieldsValue["f78"], config.FieldsValue["f78"], properties.FieldsValue["f10"]
    require(len(set(roles)) == 3, "renderer source collapsed the actual appearance owner identities")
    return tuple(carries_render(value) for value in roles), managers, {
        **summary, "physical_density_parameter": density, "active_configuration_density": config.FieldsValue["fc50"]}


def project_look(model, config, holder, managers):
    state = managers.AppearanceValue
    require(model == config, "renderer source alters its active selected configuration appearance")
    mat = model["f20"]
    rv, pbr = mat["f90"], model["f88"]
    source = PureWindowsPath(rv["f68"])
    name = str(source.parent.parent.parent)
    require(rv["f68"] == name + "\\" + RESOURCE
            and holder["f20"]["f90"]["f68"] == r"<SystemTexture>" + "\\" + RESOURCE,
            "renderer source requires a consistent live and detached resource alias")
    held, live = material_id(holder), material_id(model)
    require(state.ManagerOnWire and 0 < held < live and live + 1 == state.NextAppearanceId,
            "renderer source has a conflicting independent Definition allocator")
    input_value = PartLookInput(
        name, RESOURCE, state.NextAppearanceId, managers.BomOnWire, rgb(model["f0c"]), rgb(model["f18"]), mat["f20"], mat["f48"],
        ClassicLook(rv["f08"], rv["f10"], rv["f40"], rv["f44"], rv["f74"], rv["f88"], rv["f8c"],
                    bool(rv["f9c"] & 0x40), bool(rv["f9c"] & 0x100)),
        BasicPbrInput(pbr["f00"], pbr["f08"], shader_rgb(pbr, "f10"), shader_rgb(pbr, "fdc"), shader_rgb(pbr, "f70"),
                      pbr["f28"], pbr["f2c"], pbr["f60"], pbr["f7c"], pbr["fd4"], pbr["fe8"], pbr["f104"],
                      bool(pbr["fd0"] & 1), bool(pbr["fcc"])),
    )
    predicted = tuple(MakeRenderLook(input_value, Holder=value).FieldsValue for value in (False, False, True))
    for label, actual, expected in zip(("model", "configuration", "holder"), (model, config, holder), predicted, strict=True):
        typed_changes = set(differences(expected, actual)) - {"f20.f90.f00", "f20.f90.f04"}
        if typed_changes:
            key = min(typed_changes)
            raise ValueError(f"unrepresented renderer source field {label}.{key}")
    return input_value, {"holder_id": held, "model_and_configuration_id": live,
                         "definition_next_appearance_id": state.NextAppearanceId, "empty_bom_present": managers.BomOnWire}


def differences(left, right, root=""):
    if type(left) is dict and type(right) is dict:
        for name in sorted(left.keys() | right.keys()):
            if name not in left or name not in right:
                yield root + name
            else:
                yield from differences(left[name], right[name], root + name + ".")
    elif left != right:
        yield root[:-1]


def request_look(archive, registry):
    looks, manager, receipt = observe_looks(archive, registry)
    input_value, identities = project_look(*looks, manager)
    return asdict(input_value), {"roles": identities, "store": receipt, "mapped_payload_equal": True}


def confirm_look(archive, registry, request):
    input_value = from_json(request)
    (model, config, actual_holder), actual_manager, store = observe_looks(archive, registry, generated=True)
    wanted_holder = MakeRenderLook(input_value, Holder=True).FieldsValue
    wanted_live = MakeRenderLook(input_value, Holder=False).FieldsValue
    holder, live, wanted_manager = PlanLookIds(input_value)
    require(model == config == wanted_live and actual_holder == wanted_holder
            and (material_id(actual_holder), material_id(model)) == (holder, live)
            and actual_manager == wanted_manager,
            "rendered child archive changed its actual visual or allocator state")
    return {**store, "holder_id": holder, "model_and_configuration_id": live,
            "definition_next_appearance_id": actual_manager.AppearanceValue.NextAppearanceId,
            "empty_bom_present": actual_manager.BomOnWire,
            "primary_rgb": rgb(model["f0c"]),
            "classic_roughness": model["f20"]["f90"]["f74"],
            "dspbr_roughness": model["f88"]["f2c"],
            "refraction_index": model["f88"]["fd4"], "reflectance": model["f88"]["f12c"],
            "live_asset": model["f20"]["f90"]["f68"],
            "holder_asset": actual_holder["f20"]["f90"]["f68"],
            "exact_payload": True}
