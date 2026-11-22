from dataclasses import replace
from pathlib import Path
from subprocess import run
import sys
from xml.etree.ElementTree import SubElement

from SweepSdkRead import prove_saved_boundary, reject_source
from convert import open_document
from convert.adapters.solidworks.Archive.Construction.Metadata.FrameKeywords import FrameKeywords
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt
from convert.adapters.solidworks.Container.Format import KeywordsStream, KPartitionStream
from convert.adapters.solidworks.Core.Native import ParseXml
from interchange.document.Models.DocumentModel import CadDocument

CONTROL = "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6"


def prove_saved_envelope(payload, repository):
    from hashlib import sha256

    generated = SldprtArchive.from_bytes(payload)
    raw = (repository / "re/solidworks/v2026/corpus/ladder/L1_boss.SLDPRT").read_bytes()
    if sha256(raw).hexdigest() != CONTROL:
        raise ValueError("saved dispatch control identity changed")
    partition = SldprtArchive.from_bytes(raw).require(KPartitionStream)
    streams = dict(generated.streams) | {KPartitionStream: partition}
    envelope = build_sldprt(streams, FormatVersion=4)
    dispatch = prove_saved_boundary(envelope, genuine_sweep=False)
    reject_source(envelope, "configuration 'Absent' is unavailable", configuration="Absent")
    root = ParseXml(streams[KeywordsStream])
    SubElement(root, "Configuration", {"Name": "Alternate", "id": "1"})
    streams[KeywordsStream] = FrameKeywords(root, False)
    alternate = build_sldprt(streams, FormatVersion=4)
    reject_source(alternate, "native data for configuration 1 is unavailable", configuration="Alternate")
    return dispatch | {"transport_control_sha256": CONTROL, "selected_configuration_checks": 8}


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
