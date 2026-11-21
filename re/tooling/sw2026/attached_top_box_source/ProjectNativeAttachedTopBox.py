from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from math import isclose, isfinite
from pathlib import Path, PureWindowsPath
import sys


DRIVERS = ("Length", "Width", "Height")
FOLDERS = {
    "moCommentsFolder_c": "Comments",
    "moFavoriteFolder_c": "Favorites",
    "moHistoryFolder_c": "History",
    "moSelectionSetFolder_c": "Selection Sets",
    "moSensorFolder_c": "Sensors",
    "moDocsFolder_c": "Design Binder",
    "moDetailCabinet_c": "Annotations",
    "moSurfaceBodyFolder_c": "Surface Bodies",
    "moSolidBodyFolder_c": "Solid Bodies",
    "moEnvFolder_c": "Lights and Cameras",
    "moInkMarkupFolder_c": "Markups",
    "moEqnFolder_c": "Equations",
    "moMaterialFolder_c": "Material <not specified>",
}
DATUM_FRAMES = {
    "Front Plane": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    "Top Plane": ((1, 0, 0), (0, 0, -1), (0, 1, 0)),
    "Right Plane": ((0, 0, -1), (0, 1, 0), (1, 0, 0)),
}
DEFAULT_LIGHTS = (
    ("Ambient", "ambient", "Ambient-1", 0.5, 0.0, 0.0, None, None),
    ("Directional1", "directional", "Directional-1", 0.0, 0.4, 0.4, (0.5417, 0.7071, -0.4545), 0.0),
    ("Directional2", "directional", "Directional-1", 0.0, 0.2, 0.4, (-0.3971, 0.342, 0.8517), 0.0),
    ("Directional3", "directional", "Directional-1", 0.0, 0.2, 0.4, (-0.8067, -0.1736, -0.5649), 0.0),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def near(first, second):
    return all(isclose(x, y, rel_tol=1e-10, abs_tol=1e-8) for x, y in zip(first, second, strict=True))


def xyz(point):
    return point.x, point.y, point.z


def check_folders(roots, model):
    from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadLightInput import ReadLightInput
    from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadNotesInput import ReadNotesInput
    from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
    from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import ReadChildren
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName

    for node in roots.values():
        kind = node.ClassValue.NameValue
        if kind not in FOLDERS:
            continue
        require(ReadNativeName(node) == FOLDERS[kind], "a stock folder has an authored name or material")
        members = ReadChildren(node)
        if kind == "moDetailCabinet_c":
            notes = ReadNotesInput(members)
            require((notes.HeadName, notes.EndName) == ("Notes", "Notes1___EndTag___"), "source has authored notes")
        elif kind == "moEnvFolder_c":
            require(node is model.FieldsValue["f1e0"], "the source environment is not the model owner")
            lights = tuple(ReadLightInput(member) for member in members)
            require(tuple((light.NameValue, light.KindValue, light.ExternalName, light.AmbientValue,
                           light.DiffuseValue, light.SpecularValue, light.DirectionValue, light.ShadowSoftness)
                          for light in lights) == DEFAULT_LIGHTS
                    and all((light.ColourValue, light.KeepInScene, light.EnabledInPv, light.UseCartesian,
                             light.PvBrightness, light.PvShadows, light.PvQuality)
                            == (0xFFFFFF, False, False, True, 1.0, True, 16.0) for light in lights),
                    "source has authored scene lighting")
        else:
            require(not members, "a stock folder contains an unrepresented model owner: " + kind)

    relations = model.FieldsValue["f9d0"].FieldsValue
    require(all(IsLineState(relations.get(name)) for name in ("f58", "f10", "fa0"))
            and relations.get("f170") == "" and relations.get("f178") == relations.get("n1c0") == 0,
            "source has an equation, link or alternate relation owner")


def check_saved_profile(profile, loop):
    from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
    from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative

    fields = profile.FieldsValue
    require(all(fields.get(name) == 0 for name in ("f390", "f3dc", "pd_has_fe8", "pd_f118", "f42c"))
            and fields["pd_f100"] == 4 and fields["pd_f11c"] == -1
            and all(fields.get(name) is None for name in ("orig_dim_feature", "f3b8", "pd_f110", "f388"))
            and all(IsLineState(fields.get(name)) for name in ("f3e8", "pd_f128", "pd_f148")),
            "source profile has another authoring or dependency owner")
    contours = fields["ca30"]
    require(contours["f10"] == 3 and contours["n238"] == 0
            and IsLineState(contours["f238"]) and IsLineState(contours["f168"]),
            "source profile has an explicit contour selection")
    cache = fields["d5c0"]
    require(fields["f3c0"] == 1 and cache["f2b0"] == cache["n2a8"] == len(cache["f2a8"]) == 1,
            "source profile is outside the saved single-contour route")
    chain = RequireNative(cache["f2a8"][0]["chain"], "moSketchChain_c").FieldsValue
    line_ids = {line.IndexValue for line in loop.LinesValue}
    require(chain["f08"]["n"] == 4 and {row["v"] for row in chain["f08"]["items"]} == line_ids
            and chain["f60"] == {"n": 1, "items": [{"v": 0}]} and len(loop.RegionValues) == 1
            and chain["nmap"] == 0 and not chain["end_map"] and chain["fc0"] is chain["fc8"] is None,
            "saved contour cache has additional or foreign boundary owners")


def check_saved_end(owner):
    from convert.adapters.solidworks.Archive.Construction.Blind.BlindZeroFields import KBlindZeroFields
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.Checks.CheckBossState import CheckBossState
    from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
    from interchange.Features.FeatureExtrude import ExtrudeEnd

    CheckBossState(owner.NodeValue)
    fields = owner.EndValue.FieldsValue
    native_save_words = {"has_f28", "has_f48", "f150", "f154"}
    require(owner.IsReversed and owner.ModeValue == ExtrudeEnd.KBlind and owner.SecondValue is None
            and all(fields.get(name) == 0 for name in set(KBlindZeroFields) - native_save_words)
            and fields["f128"] == 1 and fields["f140"].FieldsValue == {"t": 0}
            and all(fields.get(name) is None for name in ("f20", "f90", "fc8", "fd0", "f138"))
            and fields["fa0"] == 0.0 and all(IsLineState(fields.get(name)) for name in ("fe0", "f100")),
            "source requires a nonordinary blind termination, taper or second end")
    require(owner.RequireDepth().Parameter.FieldsValue.get("f48") is None,
            "source active depth has an additional parameter expression owner")


def read_signed_intent(link, roots):
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckOriginGeom import CheckOriginGeom
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import ReadPrismFrame
    from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimGraph import CheckDimGraph
    from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadLineDims import ReadLineDims
    from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLineLoop import ReadLineLoop
    from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
    from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
    from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative

    model = link.ConfigValue.RootValue
    boss, = (value for value in roots.values() if value.ClassValue.NameValue == "moExtrusion_c")
    owner = ReadExtrude(link, boss, roots)
    check_saved_end(owner)
    profile = owner.ProfileValue
    require(owner.ParentsValue == (profile,) and not ReadParents(profile),
            "source boss or profile has another feature dependency")
    top_frame = ReadPrismFrame(profile, model, roots, FrontOnly=False)
    plane_id = profile.FieldsValue["pd_f78"].FieldsValue["ff0"]["f00"]
    require(ReadNativeName(roots[plane_id]) == "Top Plane" and xyz(top_frame.origin) == (0, 0, 0)
            and tuple(map(xyz, (top_frame.x_axis, top_frame.y_axis, top_frame.z_axis))) == DATUM_FRAMES["Top Plane"],
            "source profile does not select the actual signed Top datum")
    sketch = RequireNative(profile.FieldsValue["pd_f80"], "sgSketch")
    dims = ReadLineDims(sketch, link)
    loop = ReadLineLoop(sketch, link, dims)
    CheckDimGraph(loop, dims)
    check_saved_profile(profile, loop)
    origin = dims.OriginValue
    require(origin is not None and ReadNativeName(origin.FeatureValue) == "Origin"
            and origin.PositionValue == (0.0, 0.0), "source profile lacks the actual model-origin relation")
    CheckOriginGeom(origin.FeatureValue)
    origin_frame = ReadPrismFrame(origin.FeatureValue, model, roots)
    require(xyz(origin_frame.origin) == (0, 0, 0)
            and tuple(map(xyz, (origin_frame.x_axis, origin_frame.y_axis, origin_frame.z_axis))) == DATUM_FRAMES["Front Plane"],
            "source model origin does not retain its independent Front frame")
    depth = owner.RequireDepth().DepthValue
    drivers = {driver.NameValue: driver for driver in dims.DriverValues}
    require(set(drivers) == set(DRIVERS[:2]) and depth.name == DRIVERS[2]
            and len(loop.PointsValue) == len(loop.LinesValue) == 4
            and len(loop.RetiredRows) == 1 and not loop.RetiredPointRows,
            "source requires four rectangle edges and exactly three named drivers")
    sizes = (drivers["Length"].MetresValue * 1000.0, drivers["Width"].MetresValue * 1000.0, depth.value_mm)
    require(all(isfinite(size) and size > 0.0 for size in sizes), "source drivers must be finite positive lengths")
    length, width, _ = sizes
    points = tuple(point.PositionValue for point in loop.PointsValue.values())
    require(all(sum(near(point, expected) for point in points) == 1
                for expected in product((0.0, length), (0.0, -width))),
            "source contour disagrees with signed dimensions")
    for name, other in (("Length", (length, 0.0)), ("Width", (0.0, -width))):
        indices = drivers[name].PointValues
        require(origin.LocalIndex in indices and near(loop.PointsValue[origin.LocalIndex].PositionValue, (0.0, 0.0))
                and near(loop.PointsValue[next(index for index in indices if index != origin.LocalIndex)].PositionValue, other),
                "named source driver does not bind its actual origin edge: " + name)
    return boss, profile, plane_id, top_frame, sizes


def check_public_model(document, roots, boss, profile, plane_id, frame, sizes):
    from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
    from interchange.Features.FeatureExtrude import ExtrudeFeature
    from interchange.Records.RecordParameter import ParameterValue

    require(str(document.units) == "mm" and not (document.assembly or document.DrawingValue
            or document.materials or document.meshes or document.diagnostics),
            "strict source read contains a failed or unrepresented model domain")
    (config,) = document.configurations
    manager = document.metadata["solidworks.typed_configuration_manager"]
    (native_config,) = manager["configurations"]
    require(manager["status"] == "complete" and config.name == native_config["name"] == "Default" and config.active
            and config.parent_id is None and not (config.overrides or config.suppressed_feature_ids)
            and native_config["native_class"] == "moPartConfiguration_c"
            and native_config["selected_by_f360"] and native_config["selected_by_f368"]
            and not any(native_config[name] for name in ("comment", "alternate_name", "feature_description")),
            "source requires one ordinary active Default configuration")
    require(document.metadata["solidworks.part_text_properties"]["status"] == "complete"
            and not document.metadata["document_summary"] and not document.metadata["custom_properties"]
            and not config.attributes["custom_properties"]
            and config.attributes["native_properties"]["Material"] == "Material <not specified>",
            "source has an unrepresented property or assigned material")
    require(len(document.feature_timeline) == len(roots) and all(not row.suppressed for row in document.feature_timeline)
            and {row.attributes["native_object_id"] for row in document.feature_timeline} == set(roots),
            "public and typed roots disagree on the actual feature graph")
    public = {row.attributes["native_object_id"]: row for row in document.feature_timeline}
    boss_row, profile_row = (public[NativeNodeId(node)] for node in (boss, profile))
    (sketch,) = document.sketches
    planes = {plane.name: plane for plane in document.support_planes}
    require(set(planes) == set(DATUM_FRAMES) and len(document.support_planes) == 3
            and all(xyz(plane.transform.origin) == (0, 0, 0) and plane.support_selection_id is None
                    and plane.offset_parameter_id is None
                    and tuple(map(xyz, (plane.transform.x_axis, plane.transform.y_axis, plane.transform.z_axis))) == DATUM_FRAMES[name]
                    for name, plane in planes.items())
            and planes["Top Plane"].transform == frame and sketch.support_plane_id == "sldprt:plane:" + str(plane_id),
            "strict public frame disagrees with the typed Top support")
    require(boss_row.name == ReadNativeName(boss) == "AdditiveBox"
            and profile_row.name == sketch.name == ReadNativeName(profile) == boss_row.name + " Profile"
            and boss_row.sketch_id == profile_row.sketch_id == sketch.id and not sketch.suppressed,
            "source does not own the measured sketch and boss tree")
    length, width, height = sizes
    require(isinstance(boss_row.definition, ExtrudeFeature)
            and boss_row.definition == ExtrudeFeature(length=ParameterValue(height, "length", "mm"), reversed=True),
            "strict public boss disagrees with the typed reversed blind end")
    parameters = {parameter.name: parameter for parameter in document.parameters}
    require(len(document.parameters) == 3 and set(parameters) == set(DRIVERS), "source contains other named parameters")
    for name, owner, size in zip(DRIVERS, (profile_row, profile_row, boss_row), sizes, strict=True):
        parameter = parameters[name]
        require(parameter.owner_id == owner.id and parameter.id in owner.parameter_ids and parameter.expression is None
                and str(parameter.role) == "driving" and parameter.value == ParameterValue(size, "length", "mm"),
                "strict public driver disagrees with its actual owner: " + name)
    (selection,) = document.selections
    require(dict(selection.query) == {"native_owner_id": NativeNodeId(boss),
                                      "native_target_id": NativeNodeId(profile), "topology_role": "direction_axis"}
            and len(selection.path) == 1 and selection.path[0].subelement == "N_Axis",
            "source contains a nonordinary direction or extra selection")
    (body,) = document.bodies
    native_body = body.attributes["solidworks.native_body"]
    require(body.name == "Body" and body.final_feature_id == boss_row.id and body.material_id is None
            and body.topology.solid_count == 1 and native_body["status"] == "complete"
            and native_body["complete_brep_binding"] and native_body["body_count"] == 1
            and native_body["last_modifying_feature_id"] == NativeNodeId(boss),
            "source body is not the actual ordinary solid owned by the boss")
    shape = document.brep
    require(shape is not None and tuple(len(getattr(shape, name)) for name in ("vertices", "edges", "faces", "shells", "bodies"))
            == (8, 12, 6, 1, 1), "strict source boundary is not a single box solid")
    points = tuple(xyz(vertex.point) for vertex in shape.vertices)
    require(all(sum(near(point, expected) for point in points) == 1
                for expected in product((0.0, length), (-height, 0.0), (0.0, width))),
            "strict source boundary disagrees with independently projected signed geometry")
    return config, boss_row, body


def project(source_bytes, expected_sha256, *, part_name):
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.LowerBoxModel import LowerBoxModel
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from interchange import CadDocument, CadSource, Configuration, DesignBody, FeatureStep, SupportPlane

    require(type(source_bytes) is bytes and sha256(source_bytes).hexdigest() == expected_sha256,
            "source bytes differ from the supplied immutable SHA-256")
    archive = SldprtArchive.from_bytes(source_bytes)
    link = ReadNativeLink(archive, 0)
    roots = IndexFeatures(link)
    expected = {**dict.fromkeys(FOLDERS, 1), "moRefPlane_c": 3, "moOriginProfileFeature_c": 1,
                "moProfileFeature_c": 1, "moExtrusion_c": 1}
    require(Counter(node.ClassValue.NameValue for node in roots.values()) == expected,
            "source contains an extra or missing authored native feature owner")
    check_folders(roots, link.ConfigValue.RootValue)
    boss, profile, plane_id, frame, sizes = read_signed_intent(link, roots)
    document = open_document(source_bytes, source_format="solidworks.sldprt", strict=True,
                             include_brep=True, include_tessellation=False)
    require(document.source.sha256 == expected_sha256, "strict public read did not use the verified source")
    config, boss_row, body = check_public_model(document, roots, boss, profile, plane_id, frame, sizes)
    semantic_sha = sha256(json.dumps([part_name, config.name, boss_row.name, body.name, sizes], allow_nan=False).encode()).hexdigest()
    seed = CadDocument(
        source=CadSource("kit.neutral.box", "<signed-top-box>", semantic_sha),
        configurations=(Configuration("box:default", config.name, active=True),),
        parameters=(),
        support_planes=(SupportPlane("box:top", "XZ-plane", frame),),
        sketches=(),
        selections=(),
        feature_timeline=(FeatureStep("box:boss", boss_row.name, "primitive", 0),),
        bodies=(DesignBody("box:body", body.name, "box:boss"),),
        units=document.units,
    )
    return LowerBoxModel(seed, part_name, tuple("box:" + name.casefold() for name in DRIVERS), sizes,
                         DRIVERS, body.name, TopAttached=True)


def main():
    parser = ArgumentParser(description="Project a locked ordinary signed Top box to the clean neutral writer request")
    parser.add_argument("source", type=Path)
    parser.add_argument("sha256")
    parser.add_argument("--native-path", required=True)
    parser.add_argument("--creation-epoch", type=int, required=True)
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    root = (args.root or Path(__file__).resolve().parents[4]).resolve(strict=True)
    sys.path.insert(0, str(root / "src"))

    from interchange.serialization.EncodeData import ToData

    require(not args.source.is_symlink() and args.source.suffix.casefold() == ".sldprt",
            "expected an immutable native part file")
    model = project(args.source.read_bytes(), args.sha256, part_name=PureWindowsPath(args.native_path).stem)
    print(json.dumps({"document": ToData(model), "native_path": args.native_path,
                      "creation_epoch": args.creation_epoch}, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
