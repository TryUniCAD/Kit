from dataclasses import replace
from pathlib import Path
from subprocess import run
import sys
from xml.etree.ElementTree import SubElement

from SweepSdkRead import prove_saved_boundary, reject_source
from convert import open_document
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Construction.Metadata.FrameKeywords import FrameKeywords
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt
from convert.adapters.solidworks.Container.Format import (
    KConfigStream, KeywordsStream, KPartitionStream, KResolvedFeaturesStream,
)
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from convert.adapters.solidworks.Core.Native import ParseXml
from interchange.document.Models.DocumentModel import CadDocument

CONTROL = "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6"


def prove_saved_envelope(payload, repository):
    from hashlib import sha256

    generated = SldprtArchive.from_bytes(payload)
    raw = (repository / "re/solidworks/v2026/corpus/ladder/L1_boss.SLDPRT").read_bytes()
    if sha256(raw).hexdigest() != CONTROL:
        raise ValueError("saved dispatch control identity changed")
    control = SldprtArchive.from_bytes(raw)
    streams = dict(generated.streams) | {KPartitionStream: control.require(KPartitionStream)}
    envelope = build_sldprt(streams, FormatVersion=4)
    dispatch = prove_saved_boundary(envelope, genuine_sweep=False)
    root = ParseXml(streams[KeywordsStream])
    declared = SubElement(root, "Configuration", {"Name": "Alternate", "id": "1"})
    root.remove(declared)
    root.insert(0, declared)
    streams[KeywordsStream] = FrameKeywords(root, False)
    declaration_only = build_sldprt(streams, FormatVersion=4)
    reject_source(declaration_only, "configuration 'Absent' is unavailable", configuration="Absent")
    reject_source(declaration_only, "native data for configuration 1 is unavailable", configuration="Alternate")
    lane_roles = (KConfigStream, KPartitionStream, KResolvedFeaturesStream)
    unrelated = {name: control.require(name) for name in lane_roles}
    multi = build_sldprt(streams | alternate_keys(unrelated), FormatVersion=4)
    for configuration in (None, "Default"):
        reject_source(multi, "unsupported SOLIDWORKS saved sweep result partition", configuration=configuration)
    check_other_lane(multi, "Alternate", 1, "Contents/Config-1-ResolvedFeatures")
    control_keywords = ParseXml(control.require(KeywordsStream))
    SubElement(control_keywords, "Configuration", {"Name": "Alternate", "id": "1"})
    SubElement(control_keywords, "Sweep", {"Name": "OrdinarySweptBoss", "id": "1000"})
    reversed_lanes = unrelated | alternate_keys({name: streams[name] for name in lane_roles})
    inverse = streams | reversed_lanes | {KeywordsStream: FrameKeywords(control_keywords, False)}
    check_other_lane(build_sldprt(inverse, FormatVersion=4),
                     "Default", 0, KResolvedFeaturesStream)
    return dispatch | {
        "transport_control_sha256": CONTROL, "selected_configuration_checks": 24,
        "multi_config_saved_refusals": 8, "unrelated_physical_lane_reads": 8,
    }


def alternate_keys(lanes):
    return {name.replace("Config-0", "Config-1"): data for name, data in lanes.items()}


def check_other_lane(payload, name, native_id, resolved_stream):
    for geometry in (True, False):
        settings = ReadOptions(configuration=name, include_brep=geometry)
        document = open_document(payload, configuration=name, include_brep=geometry)
        direct = SldprtAdapter().read(payload, settings)
        active, = (row for row in document.configurations if row.active)
        if (document != direct or active.name != name
                or active.attributes["native_configuration_id"] != native_id
                or not any(span.stream == resolved_stream for step in document.feature_timeline
                           if step.provenance is not None for span in step.provenance.spans)
                or (document.brep is not None) != geometry):
            raise ValueError("explicit alternate scope did not use its actual unrelated physical lane")


def prove_cli_transfer(payload, repository, folder):
    source, target = (Path(folder) / label for label in ("Source.SLDPRT", "Transfer.json"))
    source.write_bytes(payload)
    result = run(
        (sys.executable, "-I", "-B", "-c",
         "import runpy, sys; sys.path.insert(0, sys.argv.pop(1)); runpy.run_module('convert', run_name='__main__')",
         str(repository / "src"), "convert", str(source), str(target),
         "--from", "solidworks.sldprt", "--to", "interchange.json"),
        cwd=repository, capture_output=True, text=True, timeout=30, check=False,
    )
    if result.returncode or result.stderr or not target.is_file():
        raise ValueError("typed sweep CLI did not reach the neutral JSON writer: " + (result.stderr or result.stdout))
    expected = open_document(payload, source_format="solidworks.sldprt")
    actual = CadDocument.from_json(target.read_text(encoding="utf-8"))
    actual.assert_valid()
    if actual != replace(expected, source=replace(expected.source, path=actual.source.path)):
        raise ValueError("neutral CLI transfer lost actual sweep, geometry or source identity")
    return {"neutral_round_trip": True, "whole_semantic_document_equal": True}
