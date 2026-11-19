from io import BytesIO
from hashlib import sha256
from pathlib import PureWindowsPath
import codecs
import json
import argparse
import sys

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHdrMut import ReadMgrHdrMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CheckCylSide import CheckCylSide
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CylChild import CylChild
from convert.adapters.solidworks.Core.TypedMates.Cylinders.PickCylFace import PickCylFace
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylAttr import ReadCylAttr
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylNodes import ReadCylNodes
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylOwner import ReadCylOwner
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylWords import ReadCylWords
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyScalar import ReadBodyScalar
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadOutputAtom import ReadOutputAtom
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from FreshCylinderInput import make_document
from para.Partition import read_partition
from para.Tracking import signed_dword
from para.cylinder.CylinderAttachment import attach_cylinder_mut
from para.rectangle.Allocate import DeltaEvent, MarkEvent, Session, Update
from para.rectangle.ArchiveAttachment import FeatureUpdate


def readback(attached, earlier):
    raw = attached.file_bytes
    archive = SldprtArchive.from_bytes(raw)
    assert dict(archive.streams) == attached.streams
    link = ReadNativeLink(archive, 0)
    nodes = ReadCylNodes(archive)
    face, surface, body = PickCylFace(nodes)
    attrs = {name: ReadCylAttr(nodes, body, name) for name in ("ATOM_ID_2001", "BODY_MATCH", "ENT_TIME_STAMP_2001")}
    atom_id = ReadBodyScalar(nodes, attrs, "ATOM_ID_2001", 1)
    boss, marker = ReadCylOwner(link, atom_id)
    CheckCylSide(CylChild(link, nodes, face, surface, boss, marker, atom_id, sha256(raw).hexdigest()))
    atom = ReadOutputAtom(boss)
    model, fields = link.ConfigValue.RootValue.FieldsValue, boss.FieldsValue
    assert model["fd88"]["atoms"][0]["o"] is atom is model["ffe0"][0]["k"]
    assert fields["f498"] == [{"v": atom_id}] and atom_id == attached.atom_id
    tag = ReadBodyScalar(nodes, attrs, "BODY_MATCH", 0)
    assert tag == atom.FieldsValue["f180"] == atom.FieldsValue["f1b0"] == attached.body_tag
    assert ReadBodyScalar(nodes, attrs, "ENT_TIME_STAMP_2001", 1) == signed_dword(link.ConfigValue.HeaderValue.FieldsValue["f44"])
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000).RootValue
    manager_header = ReadMgrHdrMut(archive.require("Contents/CMgrHdr2"), 19000).RootValue
    config_header = manager_header.FieldsValue["f08"]["items"][0]["o"].FieldsValue
    assert config_header["f38"] == manager.FieldsValue["f360"].FieldsValue["f860"] == link.ConfigValue.HeaderValue.FieldsValue["f40"]
    assert config_header["f50"] == model["f1300"]
    p = read_partition(archive.require(KPartitionStream))
    selected, _, activation = p.history
    assert selected.mark.fields["id"] == fields["f3d0"].FieldsValue["f18"] == attached.selected_mark
    assert activation.mark.fields["id"] == model["fe38"].FieldsValue["f18"] == attached.activation_mark
    assert face.Integer("node_id") == attached.lateral_face_node_id != face.IndexValue
    assert ReadCylWords(nodes, face, 3) == (earlier + 3, 0)
    return {"body_tag": tag, "atom_id": atom_id, "face_node_id": face.Integer("node_id"),
            "marks": [attached.activation_mark, attached.selected_mark], "role_index": face.IndexValue,
            "archive_sha256": sha256(raw).hexdigest(), "archive_bytes": len(raw),
            "stream_sha256": {name: sha256(value).hexdigest() for name, value in archive.streams.items()}}


def run(variant):
    shape = (3.25, -8.25, 4.25, 21.875) if variant == 1 else (-8.75, 2.375, 8.625, 16.125)
    name = "BoundCylinder" + str(variant)
    stamp = 1815300101 + 200 * variant
    spec = {"name": name, "axis": "z", "plane": "Front Plane", "center_mm": shape[:2],
            "radius_mm": shape[2], "depth_mm": shape[3], "driver": "diameter", "reversed": False}
    doc = make_document(spec)
    doc.AssertValid()
    GetDocumentCaps(doc)
    options = WriteOptions(values={"final_destination": str(PureWindowsPath("C:/KitResearch", name + ".SLDPRT"))})
    session = Session(1137 + 1148 * variant, 26 + 91 * variant,
                      (DeltaEvent("activation"), MarkEvent("activation", "activation", True),
                       DeltaEvent("intervening"), MarkEvent("intervening", "intervening", False),
                       DeltaEvent("geometry"), MarkEvent("geometry", "geometry", True)),
                      (Update.ADVANCE, Update.ADVANCE, Update.ADVANCE, Update.ATTACH_BODY, Update.TESSELLATE),
                      stamp, 1159 * variant)
    events = tuple(FeatureUpdate(i, stamp, i + 1, True) for i in range(3))
    earlier = 7 * variant
    for encoding in ("utf-16-le", "utf-16-be", "cp1252"):
        codecs.lookup(encoding)
    active = True
    attempts = []

    def guard(event, values):
        if active and event in {"open", "subprocess.Popen", "socket.connect", "os.system", "os.posix_spawn"}:
            attempts.append(event)
            raise RuntimeError("runtime operation during guarded construction: " + event)
    sys.addaudithook(guard)
    try:
        baseline = PrepareNative(doc, BytesIO(), stamp, options)
        prepared = PrepareNative(doc, BytesIO(), stamp, options)
        attached = attach_cylinder_mut(prepared, session, events, earlier)
        repeat = attach_cylinder_mut(PrepareNative(doc, BytesIO(), stamp, options), session, events, earlier)
        assert repeat == attached
        try:
            attach_cylinder_mut(prepared, session, events, earlier)
        except ValueError as exc:
            assert str(exc) == "source must have an unused ordinary output and live-body map"
        else:
            raise RuntimeError("second attachment unexpectedly accepted")
        receipt = readback(attached, earlier)
        changed = sorted(name for name in attached.streams if baseline.StreamsValue.get(name) != attached.streams[name])
    finally:
        active = False
    assert not attempts
    assert changed == ["Contents/CMgr", "Contents/CMgrHdr2", "Contents/Config-0", "Contents/Config-0-ModelHeader",
                       "Contents/Config-0-Partition", "Contents/Config-0-ResolvedFeatures", "Header2"]
    return {**receipt, "changed_streams": changed, "runtime_io_attempts": len(attempts), "source": spec,
            "second_attachment_refused": True, "same_process_repeat_exact": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("case", type=int, choices=(1, 2))
    args = parser.parse_args()
    print(json.dumps(run(args.case), indent=2, sort_keys=True, allow_nan=False))
