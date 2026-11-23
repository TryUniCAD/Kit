from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeyDisplay import MakeKeyDisplay
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.Units.ReadPartUnitNodes import ReadUnitNodes


def read_link(archive):
    try:
        return ReadNativeLink(archive, 0)
    except BodyUnsupported as error:
        if str(error).endswith("moSweep_c schema 1"):
            return ReadNativeLink(archive, 0, SavedSweep=True)
        if not str(error).endswith("uoMaterialTextureProperties.restore"):
            raise
    config_name = "Contents/Config-0"
    stream_name = config_name + "-ResolvedFeatures"
    header = ReadHeaderGraph(archive.require(config_name + "-ModelHeader"), 19000)
    config = ReadConfigMut(archive.require(config_name), 19000, header, ReadMaterial=True)
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000, ReadMaterial=True)
    resolved = ReadResolvedMut(archive.require(stream_name), 19000, config.MapValue,
                               MakeLinkContext(config, manager))
    return NativeLink(config, resolved, config_name, stream_name, manager)


def sketch_dimensions(sketch):
    values = sketch.FieldsValue["dims"]
    displays = values.get("f118")
    if displays is None:
        return
    for item in displays.FieldsValue["items"]:
        display = item["o"]
        link, = display.FieldsValue["f850"]
        handle = link["o"]
        group = {"moSkDimHandleValG2_c": "val_g2",
                 "moSkDimHandleRadial_c": "val_g1"}[handle.ClassValue.NameValue]
        if handle.FieldsValue["ff0"] is not sketch:
            raise ValueError("dimension display targets a distinct sketch")
        yield values[group][handle.FieldsValue["ff8"]]["d"]


def end_dimensions(feature_kind, end):
    fields = end.FieldsValue
    for lane in ("f18", "f20"):
        if feature_kind != "moRevolution_c":
            primary, secondary = fields["f0c"], fields["f10"]
            no_length = {1, 2, 3, 4, 9}
            if lane == "f18" and primary in no_length:
                continue
            if lane == "f20" and (fields["f08"] != 0 or primary == 6 or secondary in no_length):
                continue
        display = fields.get(lane)
        if display is not None:
            handle, = display.FieldsValue["f850"]
            yield handle["o"].FieldsValue["ff0"]


def feature_dimensions(feature):
    kind = feature.ClassValue.NameValue
    if kind == "moProfileFeature_c":
        yield from sketch_dimensions(feature.FieldsValue["pd_f80"])
    elif kind in ("moICE_c", "moExtrusion_c", "moRevolution_c"):
        end_field = "f8d8" if kind == "moRevolution_c" else "f818"
        yield from end_dimensions(kind, feature.FieldsValue[end_field])


def project_dimensions(archive):
    linked = read_link(archive)
    units = ReadUnitNodes(linked.ConfigValue.RootValue)
    result = {}
    keys = {}
    for feature in linked.ResolvedValue.RootsValue:
        if not isinstance(feature, ArchiveNode):
            continue
        rows = []
        ids = []
        for dimension in feature_dimensions(feature):
            parameter = dimension.FieldsValue["f28"]
            angle = parameter.ClassValue.NameValue == "moAngleParameter_c"
            if not angle and parameter.ClassValue.NameValue != "moLengthParameter_c":
                raise ValueError("unclassified keyword parameter class")
            policy = units["angle" if angle else "length"].FieldsValue
            if policy["fb0"] != 0:
                raise ValueError("unclassified physical display unit")
            glyph = None
            if dimension.ClassValue.NameValue == "sgCircleDim":
                glyph = {3: "radius", 15: "diameter"}[dimension.FieldsValue["f80"]]
            rows.append(MakeKeyDisplay(ReadNativeName(parameter), parameter.FieldsValue["f58"],
                                       "degree" if angle else "mm",
                                       DisplayPlaces=policy["f0c"], GlyphValue=glyph))
            ids.append(parameter.FieldsValue["f08"])
        if rows:
            identifier = feature.FieldsValue["f08"]
            if identifier in result:
                raise ValueError("duplicate model feature identity")
            result[identifier] = tuple(rows)
            keys[identifier] = tuple(ids)
    return result, keys
