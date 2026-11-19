from codecs import lookup
from hashlib import sha256
from json import dumps, loads
from math import isclose
from pathlib import Path, PureWindowsPath
from sys import addaudithook
from argparse import ArgumentParser

from convert.adapters.solidworks.Archive.Construction.Part.MakePolygonBlindPart import MakePolygonBlindPart
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.serialization.Deserialize import FromData
from interchange.document.Validation.DocumentValidate import AssertValid
from tests.Convert.Solidworks.Research.Construction.Part.MakePolygonCase import MakePolygonCase
from PrepareSdkPolygonCohort import prism as expected_prism
from SdkBlindPartSettings import settings
from para.Partition import read_partition, frame_payloads, write_payloads
from para.concentric.CylinderFace import words
from para.prism.SdkPrismAttachment import attach_sdk_prism
from para.rectangle.ArchiveAttachment import FeatureUpdate
from para.rectangle.CheckProjection import schedule
from para.rectangle.RectangleAttributes import Appearance

def main():
    parser = ArgumentParser()
    parser.add_argument("case", type=int, choices=(1, 2))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--windows-root", type=PureWindowsPath, required=True)
    parser.add_argument("--authored-light", type=Path, required=True)
    args = parser.parse_args()
    packet = args.output
    packet.mkdir()
    guest = args.windows_root
    if not guest.is_absolute():
        raise ValueError("the physical Windows destination must be absolute")
    light = loads(args.authored_light.read_bytes())
    for encoding in ("utf-8", "utf-16-le", "utf-16-be", "latin-1", "cp1252"):
        lookup(encoding)
    shapes = (
        ("SdkPrismRectangle", ((-3.6,-6.7),(35.1,-6.7),(35.1,12.8),(-3.6,12.8))),
        ("SdkPrismConcave", ((0.0,25.0),(13.0,25.0),(13.0,9.0),(27.0,9.0),(27.0,0.0),(0.0,0.0))),
    )
    active = False
    attempts = []
    def audit(event, arguments):
        if active and event in ("open","subprocess.Popen","os.system","os.posix_spawn","socket.connect"):
            attempts.append(event)
            raise RuntimeError("unexpected construction IO: " + event)
    addaudithook(audit)
    records = []
    index = args.case - 1
    name, points = shapes[index]
    job = MakePolygonCase(name, points, bool(index))
    target = packet / f"{name}.SLDPRT"
    job["settings"]["output"]["path_name"] = str(guest / target.name)
    request = dumps(job,sort_keys=True,indent=2) + "\n"
    (packet / f"{name}.Neutral.json").open("x", encoding="utf-8").write(request)
    document = FromData(job["document"])
    AssertValid(document)
    active = True
    try:
        native = settings(job["settings"])
        candidate = MakePolygonBlindPart(document, native)
        base = dict(candidate.StreamsValue)
        epoch = max(job["settings"]["provenance"][item] for item in ("created_at","modified_at","updated_at")) + 7
        session = schedule(2383 + index * 461, 21, 1, 0, 5, 2, 0, epoch, 930116 + 2 * index)
        events = (
            FeatureUpdate(1, epoch, 138811, False),
            FeatureUpdate(4, epoch, 348991, True),
            FeatureUpdate(8, epoch, 583111, True),
        )
        attached = attach_sdk_prism(candidate, session, events, Appearance((43,116,153), 0.11, 1000.0), light)
        archive = SldprtArchive.from_bytes(attached.candidate.BytesValue)
        assert archive.streams == attached.candidate.StreamsValue
        assert set(archive.streams) - set(base) == {KPartitionStream}
        partition_stream = archive.require(KPartitionStream)
        geometry = read_partition(partition_stream)
        assert frame_payloads(write_payloads(geometry)) == partition_stream
        assert len([node for node in geometry.nodes if node.kind == 14]) == len(points) + 2
        linked = ReadNativeLink(archive,0)
        model = linked.ConfigValue.RootValue
        producer, = (root for root in linked.ResolvedValue.RootsValue if root is not None and root.ClassValue.NameValue == "moExtrusion_c")
        atom, = (row["o"] for row in model.FieldsValue["fd88"]["atoms"])
        assert producer.FieldsValue["f528"]["items"][0]["o"] is atom
        assert producer.FieldsValue["f498"] == [{"v": atom.FieldsValue["f140"]}]
        nodes = {node.index: node for node in geometry.nodes}
        body, = (node for node in nodes.values() if node.kind == 12)
        atom_id, = words(nodes,body,"ATOM_ID_2001",1)
        assert atom_id == atom.FieldsValue["f140"] == attached.prism.atom_id
        sides = []
        for face in (node for node in nodes.values() if node.kind == 14):
            identity = words(nodes,face,"FACE_ID_2001",2)
            if identity[0] == 74:
                sides.append(identity[-1])
            else:
                assert identity[0] == 40 and identity[-2] in (0,1)
        assert set(sides) == {node.FieldsValue["f08"] for node in candidate.ProfileValue.GeometryValue.LineValues}
        expectation = expected_prism(points, candidate.PlanValue.DepthValue)
        assert isclose(expectation["volume_m3"],attached.prism.volume_mm3 * 1e-9,rel_tol=1e-12)
        assert isclose(expectation["area_m2"],attached.prism.area_mm2 * 1e-6,rel_tol=1e-12)
    finally:
        active = False
    target.open("xb").write(attached.candidate.BytesValue)
    records.append({"case": name, "archive_bytes": target.stat().st_size, "part_sha256": sha256(target.read_bytes()).hexdigest(),
                    "partition_sha256": sha256(partition_stream).hexdigest(), "native_feature_owner": producer.FieldsValue["f08"],
                    "body_atom_id": atom_id, "actual_sketch_segment_ids": sides, "face_count": len(points)+2,
                    "depth_m": candidate.PlanValue.DepthValue, "depth_parameter": candidate.PlanValue.DepthName + "@" + candidate.PlanValue.FeatureName,
                    "neutral_sha256": sha256(request.encode()).hexdigest(), "geometry": expectation})
    proof = {"schema":"kit.sw2026.sdk-prism-attachment-host.v1", "writer_runtime_io_attempts":len(attempts), "worker_case":args.case,
             "native_launches":0, "heldout_inputs_read":0, "records":records}
    (packet/"HostProof01.json").open("x",encoding="utf-8",newline="\n").write(dumps(proof,sort_keys=True,indent=2)+"\n")
    print(dumps(proof,sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
