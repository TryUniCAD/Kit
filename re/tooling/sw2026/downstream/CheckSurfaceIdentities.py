from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from io import BytesIO
from json import dumps
from pathlib import PureWindowsPath
from struct import pack
from sys import addaudithook

from FreshCylinderInput import make_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileText
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from downstream.Body import COLLECTIONS, ROOT
from downstream.CacheInputs import finalized_part_prefix
from downstream.Components import read_component_body, write_component_body
from downstream.Storage import ConfigurationCache, cache_path, store_part_caches
from downstream.SurfaceIdentities import cylinder_surface_identities
from para.concentric.CylinderFace import make_feature_file
from para.cylinder.CylinderAttachment import attach_cylinder_mut
from para.rectangle.Allocate import DeltaEvent, MarkEvent, Session, Update
from para.rectangle.ArchiveAttachment import FeatureUpdate


def generated_attachment(variant):
    name = f"DownstreamCylinderSurface{variant}"
    destination = str(PureWindowsPath("C:/KitResearch", name + ".SLDPRT"))
    document = make_document({
        "name": name, "axis": "z", "plane": "Front Plane", "center_mm": (2.5 * variant, -8.25),
        "radius_mm": 3.125 + variant, "depth_mm": 15.875 + 6.25 * variant, "driver": "diameter",
        "reversed": False,
    })
    stamp = 1818199455 + 230 * variant
    candidate = PrepareNative(document, BytesIO(), stamp, WriteOptions(
        values={"final_destination": destination},
    ))
    session = Session(1137 + 1148 * variant, 26 + 91 * variant,
                      (DeltaEvent("activation"), MarkEvent("activation", "activation", True),
                       DeltaEvent("intervening"), MarkEvent("intervening", "intervening", False),
                       DeltaEvent("geometry"), MarkEvent("geometry", "geometry", True)),
                      (Update.ADVANCE,) * 3 + (Update.ATTACH_BODY, Update.TESSELLATE)
                      + (Update.ADVANCE, Update.ADVANCE_BODY) * (variant - 1),
                      stamp, 1159 * variant)
    events = tuple(FeatureUpdate(i, stamp, i + 1, True) for i in range(3))
    return attach_cylinder_mut(candidate, session, events, 11 * variant), destination


def main():
    parser = ArgumentParser()
    parser.add_argument("variant", type=int, choices=(1, 2))
    variant = parser.parse_args().variant
    for encoding in ("utf-8", "utf-16le", "utf-16be", "latin-1", "cp1252"):
        lookup(encoding)
    attached, destination = generated_attachment(variant)
    child = attached.candidate
    feature = child.BossValue.FeatureValue.FieldsValue["f08"]
    birth = DatumTime(child.HeaderValue, feature)
    cfg = child.CurrentConfig
    marker = child.ProfileValue.GeometryValue.ArcValue.FieldsValue["f08"]
    events = []
    active = True

    def guard(event, args):
        if active and event in ("open", "subprocess.Popen", "socket.connect"):
            events.append(event)
            raise RuntimeError("external operation during generated surface reference replay")

    addaudithook(guard)
    try:
        feature_file = make_feature_file(child)
        surfaces = cylinder_surface_identities(attached, feature_file)
        assert len({row.node_id for row in surfaces}) == 3
        owner = feature_file.FieldsValue
        wrong_config = {**owner["refcfg"], "f10": cfg.FieldsValue["f08"] + 1}
        foreign_file = ArchiveNode(feature_file.ClassValue, {**owner, "refcfg": wrong_config})
        for rejected in (None, foreign_file):
            try:
                cylinder_surface_identities(attached, rejected)
            except ValueError:
                pass
            else:
                raise AssertionError("accepted a missing or foreign feature file owner")
        prefix = finalized_part_prefix(child, next_id=1)
        fields = prefix | {field.NameValue: [] for field in COLLECTIONS}
        fields |= {
            "f30": "", "f38_high": 0, "f38_low": 0,
            "f40": [{"object": row.representation} for row in surfaces],
        }
        body = ArchiveNode(ROOT, fields)
        state = ConfigurationCache(cfg.FieldsValue["f08"], True, False, True, body, False)
        streams = store_part_caches(child.StreamsValue, (state,))
        raw = BuildSldprt(streams, FormatVersion=4)
        archive = SldprtArchive.from_bytes(raw)
        assert archive.streams == streams
        assert all(archive.require(name) == value for name, value in child.StreamsValue.items())
        cache_bytes = archive.require(cache_path(state.storage_id))
        header_path = f"Contents/Config-{cfg.FieldsValue['f08']}-ModelHeader"
        header = ReadHeaderGraph(archive.require(header_path), 19000).FieldsValue
        assert cache_bytes[:32] == pack(
            "<8I", 1, 19000, 2026306, 19000, 2026306, header["f40"], header["f44"], header["f48"],
        )
        recovered, maps = read_component_body(cache_bytes)
        assert write_component_body(recovered)[0] == cache_bytes
        assert all(recovered.FieldsValue[name] == value for name, value in prefix.items())
        restored = [entry["object"] for entry in recovered.FieldsValue["f40"]]
        keepers = [entry.FieldsValue["f10"]["f10"] for entry in restored]
        files = [keeper.FieldsValue["f08"] for keeper in keepers]
        assert len({id(keeper) for keeper in keepers}) == 3 and len({id(file) for file in files}) == 1
        assert all(keeper.FieldsValue["f10"] == {"f00": feature, "f08": birth} for keeper in keepers)
        file = files[0].FieldsValue
        assert file["refcfg"]["f10"] == cfg.FieldsValue["f08"]
        assert ReadFileText(file["shared"]["h18"]) == destination
        side, = (entry for entry in restored if entry.ClassValue.NameValue == "moFromSktEntSurfIdRep_c")
        caps = [entry for entry in restored if entry.ClassValue.NameValue == "moEndFaceSurfIdRep_c"]
        assert side.FieldsValue["f38"] == marker
        assert sorted((cap.FieldsValue["f38"], cap.FieldsValue["f3c"]) for cap in caps) == [(0, 0), (1, 0)]
    finally:
        active = False
    print(dumps({
        "passed": True, "variant": variant, "feature_id": feature, "feature_creation": birth, "arc_marker": marker,
        "surface_node_ids": [row.node_id for row in surfaces], "object_map_counter": maps.CounterValue,
        "finalized_prefix": prefix,
        "generated_part_streams_preserved": len(child.StreamsValue), "cache_body_bytes": len(cache_bytes),
        "cache_body_sha256": sha256(cache_bytes).hexdigest(), "container_sha256": sha256(raw).hexdigest(),
        "rejected_file_owners": 2, "runtime_io_attempts": len(events), "native_runs": 0,
        "scope": "actual generated surface and file owners inside a scoped raw cache-body witness",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
