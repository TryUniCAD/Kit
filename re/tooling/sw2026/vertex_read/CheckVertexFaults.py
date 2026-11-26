from hashlib import sha256

from convert import open_document
from convert.Geometry.Parasolid import EncodePartMut, ParaHeaderData, ReadBrepResult
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Parasolid import DecodePartition

from MutateVertexInputs import numerical_faults, owner_faults


def public_refusal(raw):
    try:
        document = open_document(raw, source_format="solidworks.sldprt", strict=True,
                                 include_brep=True, include_tessellation=False)
    except ValueError as failure:
        return {"returned": False, "reason": str(failure)}
    assert document.brep is None
    return {"returned": True, "brep": False}


def repack(archive, payloads, changed):
    wire = b"".join(EncodePartMut(changed if item.kind == "partition" else item.data)
                    for item in payloads)
    streams = dict(archive.streams)
    streams["Contents/Config-0-Partition"] = wire
    return BuildSldprt(streams, FormatVersion=4)


def check_faults(root, five):
    path = root / five["path"]
    raw = path.read_bytes()
    archive = SldprtArchive.from_bytes(raw, "disclosed generated fault source")
    payloads = DecodePartition(archive.Require("Contents/Config-0-Partition"))
    active, = (item for item in payloads if item.kind == "partition")
    header = ParaHeaderData(active.data)
    assert header is not None
    bodies = {"truncated_active": active.data[:header.body_offset + 8],
              "trailing_active": active.data + b"\x00",
              "unsupported_schema": active.data.replace(b"SCH_3701250_37102_13006", b"SCH_3701250_37102_13007", 1)}
    report = {}
    for name, body in bodies.items():
        legacy, reason = ReadBrepResult(body)
        assert legacy is None, name
        report[name] = {"legacy_reason": reason, "public": public_refusal(repack(archive, payloads, body))}
    streams = dict(archive.streams)
    streams["Contents/Config-0-Partition"] = EncodePartMut(active.data)[:-1]
    report["truncated_frame"] = {"public": public_refusal(BuildSldprt(streams, FormatVersion=4))}
    def packet(changed):
        return repack(archive, payloads, changed)
    report.update(numerical_faults(active.data, packet, public_refusal, five))
    report.update(owner_faults(active.data, packet, public_refusal))
    assert path.read_bytes() == raw and sha256(raw).hexdigest() == five["sha256"]
    return report
