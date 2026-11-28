from functools import partial
from struct import pack

from ColdFilletAnno import read_annotation_binding
from FilletModel import require

from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.NormalizeCount import NormalizeCount
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount
from convert.adapters.solidworks.Archive.Counts.ReadCount import ReadCount
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Resolved.FindModelRoot import FindModelRoot
from convert.adapters.solidworks.Archive.Resolved.MakeResolvedCtx import MakeResolvedCtx
from convert.adapters.solidworks.Archive.Resolved.ReadMbsMut import ReadMbsMut
from convert.adapters.solidworks.Archive.Resolved.UseFilletCtxMut import UseFilletCtxMut
from convert.adapters.solidworks.Archive.Resolved.WriteMbsMut import WriteMbsMut
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.ReadFilletKeys import ReadFilletKeys
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative

VERSION = 19000
LINK = {"model_compressed_stream": 1, "model_is_part": 1, "cmgr_f658": 1}


def check_cold_roots(roots, model):
    require(tuple(root.ClassValue.NameValue for root in roots[-2:]) == ("moExtrusion_c", "Fillet_c")
            and sum(root.ClassValue == RuntimeClass("Fillet_c", 1) for root in roots) == 1,
            "cold fillet requires one ordinary final boss and its actual edge treatment")
    stock, fillet = roots[-2:]
    fields = fillet.FieldsValue
    require((fields["f81c"], fields["f8dc"], fields["f8e8"], fields["f8ec"], fields["f8f0"]) == (0, 1, 0, 0, 0),
            "another fillet mode needs independent typed support")
    atom = RequireNative(fields["f538"], "moAtom_c")
    (output,) = NativeRows(stock.FieldsValue["f528"]["items"])
    (member,) = NativeRows(model.FieldsValue["fd88"]["atoms"])
    require(stock.FieldsValue.get("owner", model) is fields.get("owner", model) is model
            and atom is output["o"] is member["o"]
            and atom.FieldsValue["f12c"] == stock.FieldsValue["f08"]
            and atom.FieldsValue["f130"] == fields["f08"], "cold fillet stock and feature owners differ")
    (pick,) = NativeRows(RequireNative(fields["f848"], "suObList").FieldsValue["items"])
    (item,) = NativeRows(RequireNative(fields["f868"], "suObList").FieldsValue["items"])
    wrapper = RequireNative(pick["o"], "moCompEdge_c")
    radius_item = RequireNative(item["o"], "edgeRadiusObject_c")
    radial = RequireNative(radius_item.FieldsValue["f10"], "moCompEdge_c")
    reference = RequireNative(wrapper.FieldsValue["fe8"], "moEdgeRef_c")
    require(wrapper is not radial and radial.FieldsValue["fe8"] is reference
            and (wrapper.FieldsValue["f18"], wrapper.FieldsValue["f1c"]) == (atom.FieldsValue["f140"], 0)
            and (radial.FieldsValue["f18"], radial.FieldsValue["f1c"]) == (0, 0)
            and reference.FieldsValue["f70"] == 0 and reference.FieldsValue["fe8"] == 0x200
            and reference.FieldsValue["f08"] == len(NativeRows(reference.FieldsValue["f10"])) == 4,
            "cold selection and radial driver do not share the actual stock reference")
    require(fields["n9b8"] == fields["nbf0"] == 0 and not fields["f9b8"] and not fields["fbf0"],
            "cold fillet must start with empty derived maps")
    for lane, keys in (("f820", {"f18", "ff0"}), ("f828", {"f18", "fe0"})):
        collection = fields[lane]
        require(set(collection) == keys and all(value["n"] == 0 and not value["items"]
                                                for value in collection.values()), "cold keeper collections must be present and empty")
    require(fields["fc20"]["n"] == 0 and not fields["fc20"]["items"], "cold options must start empty")
    display = RequireNative(radius_item.FieldsValue["f08"], "moDisplayRadialDim_c")
    view = display.FieldsValue
    (handle_row,) = NativeRows(view["f850"])
    handle = RequireNative(handle_row["o"], "moFeatureDimHandle_c")
    dimension = RequireNative(handle.FieldsValue["ff0"], "ThreeDRadiusDim_c")
    parameter = RequireNative(dimension.FieldsValue["f28"], "moLengthParameter_c")
    radius = parameter.FieldsValue["f58"]
    require(ReadNodeName(parameter) == "D1" and dimension.FieldsValue["f50"] > 0
            and view["f6a0"]["f10"] == 20 and view["f7f8"] == "R" and view["ffd8"] & 0x4 == 0x4
            and view["f950"] == radius and view["f5b0"]["data"] == pack("<d", radius),
            "cold fillet needs the actual live D1 radius identity and synchronized display")
    support = [row["f08"] for row in NativeRows(reference.FieldsValue["f10"])]
    historical = [RequireNative(row.FieldsValue["f10"]["f10"], "moFR_c").FieldsValue for row in support]
    require(all(row.FieldsValue["f10"]["f08"] is None for row in support)
            and all(owner["f10"]["f00"] == stock.FieldsValue["f08"] for owner in historical)
            and all(owner["f08"] is historical[0]["f08"] and owner["f10"]["f08"] == historical[0]["f10"]["f08"]
                    for owner in historical), "cold edge carriers must share the same original producing stock")
    _, self_path, config_name, config_id = ReadFilletKeys(RequireNative(historical[0]["f08"], "moExtObject_c"))
    witness = {"driver_id": dimension.FieldsValue["f50"], "driver": "D1", "radius_m": radius,
               "stock_birth": historical[0]["f10"]["f08"], "self_path": self_path,
               "config_name": config_name, "config_id": config_id, "feature_id": fields["f08"], "stock_id": stock.FieldsValue["f08"], "atom_id": atom.FieldsValue["f140"],
               "surface_keys": [(row.ClassValue.NameValue, row.FieldsValue["f38"], row.FieldsValue.get("f3c")) for row in support]}
    annotation = read_annotation_binding(model, display)
    if annotation is not None:
        witness["annotation"] = annotation
    return witness


def cold_context(seed):
    context = MakeResolvedCtx(VERSION, seed, LINK, None)
    UseFilletCtxMut(context)
    fields = context.LayoutsValue["Fillet_c"]
    require((fields[-1].KindValue, fields[-1].NameValue) == ("Validate", "OrdinaryEdgeFillet"),
            "shared fillet grammar no longer has its saved-result validation boundary")
    context.LayoutsValue = {**context.LayoutsValue, "Fillet_c": fields[:-1]}
    return context


def write_cold_resolved(roots, seed, body_map):
    witness = check_cold_roots(roots, FindModelRoot(seed))
    context = cold_context(seed)
    writer = BodyWriter(ArchiveMaps(seed.CounterValue, seed), context, WriteBodyMut)
    writer.OutputValue.extend(EncodeScalar(seed.CounterValue, "u32"))
    writer.OutputValue.extend(EncodeCount(len(roots)))
    for root in roots:
        WriteNodeMut(writer, root)
    WriteMbsMut(writer, FindModelRoot(seed), body_map)
    context.UsageValue.IsComplete = True
    return bytes(writer.OutputValue), witness, map_witness(seed, writer.MapValue.Snapshot(), roots)


def read_cold_resolved(raw, seed):
    context = cold_context(seed)
    cursor = BinaryReader(raw)
    base = cursor.ReadUnsigned(4)
    require(base == seed.CounterValue, "cold resolved stream detached from actual configuration map")
    count, cursor.OffsetValue = ReadCount(cursor.BytesValue, cursor.OffsetValue)
    reader = GraphReader(cursor, ArchiveMaps(base, seed), partial(ReadBodyMut, context))
    roots = tuple(ReadNodeMut(reader) for _ in range(NormalizeCount(count, "")))
    body_map = ReadMbsMut(context, reader, FindModelRoot(seed))
    require(not cursor.GetRemaining() and body_map == {"n": 0, "fcd8": []},
            "cold fillet resolved read must finish at its actual empty inline body map")
    return roots, check_cold_roots(roots, FindModelRoot(seed)), map_witness(seed, reader.MapValue.Snapshot(), roots)


def map_witness(seed, snapshot, roots):
    return {"base": seed.CounterValue, "end": snapshot.CounterValue, "roots": len(roots)}
