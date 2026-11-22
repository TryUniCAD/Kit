from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import CompRefFields
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakePrismNodes import MakePrismNodes
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from SweepArchiveLayout import CONTACT, CURVE, PROFILE
from SweepModel import require
from SweepSectionTransport import make_section_cells


def object_rows(*nodes):
    return {"n": len(nodes), "items": tuple({"o": node} for node in nodes)}


def node(name, fields):
    return ArchiveNode(RuntimeClass(name, 1), fields)


def curve_reference(system, header, profile, support_axis, ghost_id, sketch_d1):
    require(support_axis in ("x", "z"), "sweep reference requires the Right section or Front path")
    part = system.RootValue
    config, = system.ConfigValues
    fields = profile.FieldsValue
    support_id = NativeNodeId(system.SystemValues.PlaneValues[support_axis])
    sketch = fields["pd_f80"]
    section = support_axis == "x"
    require(profile.ClassValue == RuntimeClass("moProfileFeature_c", 1) and fields["owner"] is part
            and fields["pd_f78"].FieldsValue["ff0"]["f00"] == support_id
            and sketch_d1.DimensionValue is sketch.FieldsValue["dims"]["val_g1"][0]["d"]
            and sketch_d1.DimensionValue.FieldsValue["f80"] == (15 if section else 3)
            and sketch_d1.DimensionValue.FieldsValue["f28"] is sketch_d1.ParameterValue
            and sketch_d1.HandleValue.FieldsValue["ff0"] is sketch
            and type(ghost_id) is int and ghost_id > 0, "curve reference requires the actual same-part sketch and driver")
    profile_id = NativeNodeId(profile)
    component = CompRefFields(part.FieldsValue["f990"])
    component.update(ff0={"f00": profile_id, "f08": DatumTime(header, profile_id)}, f20=ghost_id)
    wrapper = {
        "f58": node(PROFILE, component), "f68": int(section), "f60": None, "f6c": 0,
        "f08": header.FieldsValue["f40"] if section else 101,
        "has_f10": 0, "has_f18": 0, "f0c": config.FieldsValue["f08"] if section else -1, "f20": 0,
        "f74": -12345, "f78": -12345, "f7c": -12345, "f50": 0, "f70": fields["f2b0"],
        "f34": 0, "f30": 0, "f98": 0, "f38": -1, "fb0": 0.0, "fb8": 1.0, "has_fc8": int(section),
        "fd0": 0xffffffff, "fd4": -1, "fe0": None, "fd8": None, "fe8": None,
    }
    if section:
        diameter = sketch_d1.ParameterValue.FieldsValue["f58"]
        wrapper["fc8"] = {"nodes": MakePrismNodes(make_section_cells(diameter / 2))}
    return node(CURVE, wrapper)


def path_contact(path):
    require(path.ClassValue == RuntimeClass(CURVE, 1) and path.FieldsValue["has_fc8"] == 0,
            "ordinary contact requires the single live Front path reference")
    return node(CONTACT, {
        "f50": object_rows(), "f90": 0.0, "f98": 0, "fa0": None, "fa8": 1.0,
        "fb0": 0, "fb8": 1, "fc8": -1, "fcc": 2, "fe0": None,
        "f40": 0, "f44": 0, "f48": 0, "fc0": -1.0, "fe8": path,
    })
