from hashlib import sha256
from math import isclose
from struct import pack

from FilletModel import require

from convert.Geometry.Parasolid import DecodePartData, ParaHeaderData, WritePointerMut
from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.LocalWrite.WriteXmtNodeMut import WriteXmtNodeMut
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import ReadActiveNodes
from convert.adapters.solidworks.Archive.Partition.ReadXmtHistory import ReadXmtHistory
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import ReadBodyAttrs
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyScalar import ReadBodyScalar

PARTITION = "Contents/Config-0-Partition"
SCHEMA = "SCH_3701250_37102_13006"


def active_replay(data, nodes):
    header = ParaHeaderData(data)
    stream, seen = bytearray(pack(">HI", 239, 0)), set()
    for value in nodes.values():
        WriteXmtNodeMut(stream, value, KKernelShapes[value.KindValue], seen)
    stream.extend(pack(">H", 1))
    WritePointerMut(stream, 0)
    body = data[header.body_offset:]
    require(stream == body, "active typed transmission records are not byte-identical")
    return {"record_bytes": len(body), "record_sha256": sha256(body).hexdigest(),
            "typed_nodes": len(nodes), "byte_identical": True}


def kernel_ownership(nodes, atom, observed):
    body, = (value for value in nodes.values() if value.KindValue == 12)
    attributes = ReadBodyAttrs(nodes, body)
    fields = {"ATOM_ID_2001": (1, "f140"), "BODY_MATCH": (0, "f180"),
              "LAST_BODY_MODIFYING_FEATURE_ID": (1, "f130")}
    owners = {name: ReadBodyScalar(nodes, attributes, name, index)
              for name, (index, _) in fields.items()}
    require(all(owners[name] == atom[field] for name, (_, field) in fields.items()),
            "active kernel attributes do not bind the linked stock/fillet atom")
    counts = {name: sum(value.KindValue == kind for value in nodes.values())
              for name, kind in (("faces", 14), ("edges", 16), ("vertices", 18))}
    require(counts == observed["body_counts"], "active kernel topology differs from native reopen")
    face, = (value for value in nodes.values()
             if value.KindValue == 14 and nodes[value.Integer("surface")].KindValue == 51)
    surface = nodes[face.Integer("surface")]
    radius, axis, position = (surface.FieldsValue[key] for key in ("radius", "axis", "pvec"))
    native_position, native_axis = observed["cylinder_m"][:3], observed["cylinder_m"][3:6]
    require(isclose(radius, observed["radius_m"], abs_tol=1e-12)
            and isclose(abs(sum(a * b for a, b in zip(axis, native_axis, strict=True))), 1.0, abs_tol=1e-12)
            and all(isclose(p, q, rel_tol=0.0, abs_tol=1e-12)
                    for p, q, d in zip(position, native_position, native_axis, strict=True) if not d),
            "cached cylinder radius or axis differs from native reopen")
    return {"body_node": body.IndexValue, "active_tracking": owners, "counts": counts,
            "cylindrical_face_node": face.IndexValue, "cylinder_node": surface.IndexValue,
            "cylinder": {"radius_m": radius, "axis": axis, "position_m": position}}


def audit_kernel(archive, atom, observed):
    active, history = DecodePartData(archive.require(PARTITION), PARTITION)
    require((active.kind, history.kind) == ("partition", "deltas")
            and active.schema == history.schema == SCHEMA, "unexpected cached kernel transmission framing")
    nodes = ReadActiveNodes(active.data)
    CheckXmtGraph(nodes)
    ownership = kernel_ownership(nodes, atom, observed)
    try:
        previous = ReadXmtHistory(history.data, nodes)
    except ValueError as error:
        require(str(error) == "current kernel framing differs", "changed kernel history refusal")
        history_result = {"strict_history_refused": str(error)}
    else:
        history_result = {"previous_mark": previous}
    return ownership | {"stream_sha256": sha256(archive.require(PARTITION)).hexdigest(),
                        "active_payload_sha256": active.sha256, "active_replay": active_replay(active.data, nodes),
                        "history_payload_sha256": history.sha256, "history": history_result}
