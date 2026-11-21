from struct import pack

from AuditRevEndOwners import ArchiveNode, ReadNativeLink, SldprtArchive, WriteResolMut, require
from AuditThinArchive import refusal
from ThinSavedRead import read_part

from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.Saved.BindSavedThin import BindSavedThin


def assert_unprojected(raw, diagnostic):
    archive = SldprtArchive.from_bytes(raw)
    for want_brep in (False, True):
        model = read_part(raw, want_brep)
        require(model.metadata.get("solidworks.typed_thin_revolve_semantics") is None
                and not model.metadata.get("solidworks.native_body_names"),
                "a fault escaped the public typed thin and body ownership gates")
        link = ReadNativeLink(archive, 0)
        refusal(lambda: BindSavedThin(model, archive, link), diagnostic)
    return {"refused": True, "diagnostic": diagnostic}


def modified(archive, name, payload):
    data = dict(archive.Streams)
    data[name] = payload
    return BuildSldprt(data, FormatVersion=archive.format_version)


def swap_partitions(raw, unedited, other_frame):
    archive = SldprtArchive.from_bytes(raw)
    stream = "Contents/Config-0-Partition"
    return {
        "different_body_tag": assert_unprojected(
            modified(archive, stream, SldprtArchive.from_bytes(unedited).require(stream)),
            "native body atom and feature identity domains disagree"),
        "same_body_tag_wrong_sector": assert_unprojected(
            modified(SldprtArchive.from_bytes(unedited), stream,
                     SldprtArchive.from_bytes(other_frame).require(stream)),
            "SOLIDWORKS thin cache has a vertex outside the editable sector",
        ),
    }


def resolved_fault(raw, mutate, diagnostic):
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    resolved = link.ResolvedValue
    feature, = (node for node in resolved.RootsValue
                if isinstance(node, ArchiveNode) and node.ClassValue.NameValue == "moRevolutionThin_c")
    mutate(feature)
    blob, _ = WriteResolMut(
        resolved.RootsValue, resolved.ExtraFields, 19000, link.ConfigValue.MapValue, resolved.ContextValue,
    )
    return assert_unprojected(modified(archive, link.StreamName, blob), diagnostic)


def activate_radius(feature):
    radial = feature.FieldsValue["f8f0"].FieldsValue["f48"]
    handle, = (row["o"] for row in radial.FieldsValue["f850"])
    parameter = handle.FieldsValue["ff0"].FieldsValue["f28"]
    parameter.FieldsValue["f58"] = 0.003
    radial.FieldsValue["f5b0"]["data"] = pack("<d", 0.003)


def redirect_face(feature):
    choice, = (row["o"] for row in feature.FieldsValue["f4a8"]["f48"]["items"])
    face = choice.FieldsValue["f08"]["items"][0]["o"]
    rep = face.FieldsValue["f10"][0]["f08"]
    rep.FieldsValue["f10"]["f10"].FieldsValue["f10"]["f00"] += 1


def redirect_mark(feature):
    feature.FieldsValue["f3d0"].FieldsValue["f18"] += 1


def assert_faults(edited, original, alternate):
    return {
        **swap_partitions(edited, original, alternate),
        "wrong_kernel_mark": resolved_fault(edited, redirect_mark, "kernel rollback marks differ from their archive owners"),
        "active_radius": resolved_fault(edited, activate_radius, "thin wall has unqualified parameter or display state"),
        "detached_face_producer": resolved_fault(edited, redirect_face, "thin face has an unresolved native producer"),
    }
