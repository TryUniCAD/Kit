from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from itertools import product
import json
from math import isclose
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from zlib import ZLIB_RUNTIME_VERSION

sys.path.insert(0, str(Path(__file__).resolve().parent))

from VerifyMeasuredBox import (
    EPOCH, FORMAT, RECEIPT, RECEIPT_SHA, ROOT, assert_result, check_compression,
    fingerprint, guard, prism, refuse, require,
)

from convert import open_document, write_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KLocalBodyStream
from convert.adapters.solidworks.Core.Preparation.Imports.PrepareImport import PrepareImport
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalBodyNodes import ReadLocalNodes
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange import CadDocument
from tests.Convert.Solidworks.Core.SolidworksLocalBodyTests import ShellMeasures

REFERENCE = ROOT / "re/solidworks/v2026/corpus/local-import-readback/ConcaveOwned.SLDPRT"
LOCATOR = r"C:\KitImportedProbe03\Candidates\ConcaveOwned.SLDPRT"
OUTLINE = ((7, -12), (33, -12), (33, -3), (17, -3), (17, 8), (7, 8))
STATIONS = (-4, 11)
ATTRIBUTE_ROLES = (
    "ATOM_ID_2001", "LAST_BODY_MODIFYING_FEATURE_ID", "SWIMPLICITBODYNAME_ID_U",
    "ENT_TIME_STAMP_2001", "BODY_RECIPE_2001",
)


def owners(document, archive):
    linked = ReadNativeLink(archive, 0)
    feature, = (row for row in linked.ResolvedValue.RootsValue
                if row is not None and row.ClassValue.NameValue == "moBaseBody_c")
    root = linked.ConfigValue.RootValue.FieldsValue
    atom, = root["fd88"]["atoms"]
    atom = atom["o"]
    feature_id, atom_id = feature.FieldsValue["f08"], atom.FieldsValue["f140"]
    require(feature.FieldsValue["f498"] == [{"v": atom_id}]
            and feature.FieldsValue["f528"]["items"][0]["o"] is atom
            and feature.FieldsValue["f3d0"].FieldsValue["f18"] > root["fe38"].FieldsValue["f18"],
            "linked feature lost its actual Config atom or distinct history marks")
    headers = [ReadHeaderGraph(archive.require(path), 19000).FieldsValue for path in
               ("Header2", "Contents/Config-0-ModelHeader")]
    stamp = headers[0]["f44"]
    require(all(row["f44"] == stamp and row["header"].SelfFile.PathValue == LOCATOR
                for row in headers), "headers lost their common body event or self locator")
    payload, = (row for row in document.brep_payloads if row.source_stream == KLocalBodyStream)
    nodes, _ = ReadLocalNodes(payload.data)
    body = nodes[1]
    chain = nodes[body.Integer("attribute_chains")]
    block = nodes[chain.Integer("list_block")]
    count = chain.Integer("list_length")
    entries = block.Indexes("entries")
    require((chain.KindValue, block.KindValue, count, block.Integer("n_entries")) == (70, 74, 5, 5)
            and chain.Integer("owner") == body.IndexValue
            and chain.Integer("finger_block") == block.IndexValue
            and entries[5:] == (0,) * 15
            and body.Integer("attributes_features") == entries[4],
            "BODY does not own exactly one ordered five-row attribute list")
    attributes = [nodes[index] for index in entries[:count]]
    values = {}
    for index, row in enumerate(attributes):
        definition = nodes[row.Integer("definition")]
        label = nodes[definition.Integer("identifier")]
        name = label.FieldsValue["string"]
        require((row.KindValue, definition.KindValue, label.KindValue) == (81, 80, 79)
                and row.Integer("owner") == body.IndexValue and name == ATTRIBUTE_ROLES[index]
                and row.Integer("next") == (entries[index - 1] if index else 0)
                and row.Integer("previous") == (entries[index + 1] if index < count - 1 else 0),
                "body bookkeeping left its own ordered definition and owner")
        slots = row.Indexes("fields")
        if name == "BODY_RECIPE_2001":
            require(slots == (0, 0), "empty body recipe carries extra data")
            values[name] = None
        elif name == "SWIMPLICITBODYNAME_ID_U":
            require(not slots[1] and nodes[slots[0]].KindValue == 98, "invalid typed name slot")
            values[name] = b"".join(unit.to_bytes(2, "little") for unit in
                                     nodes[slots[0]].FieldsValue["values"]).decode("utf-16-le")
        else:
            require(not slots[0] and nodes[slots[1]].KindValue == 82, "invalid typed scalar slot")
            values[name], = nodes[slots[1]].FieldsValue["values"]
    require(sum(row.KindValue == 81 for row in nodes.values()) == count
            and values == dict(zip(ATTRIBUTE_ROLES, (atom_id, feature_id, ReadNodeName(feature), stamp, None),
                                   strict=True)), "native attributes do not independently bind to linked owners")
    return {"body_attributes": values, "body_index": body.IndexValue, "kernel_nodes": len(nodes)}


def read_back(data, measured, outline=OUTLINE):
    doc = open_document(data, source_format=FORMAT, strict=True)
    archive = SldprtArchive.from_bytes(data)
    binding = owners(doc, archive)
    config, = doc.configurations
    shape = doc.brep
    body, = doc.bodies
    feature, = (row for row in doc.feature_timeline if row.kind == "imported")
    require(not doc.validate() and config.active and config.name == "Default"
            and feature.id == body.final_feature_id
            == f"sldprt:feature:{binding['body_attributes']['LAST_BODY_MODIFYING_FEATURE_ID']}"
            and body.name == feature.name == binding["body_attributes"]["SWIMPLICITBODYNAME_ID_U"]
            == "Imported geometry"
            and shape.bodies[0].design_body_id == body.id and not doc.parameters,
            "strict reader changed the source configuration or actual imported body identity")
    observed = {(vertex.point.x, vertex.point.y, vertex.point.z) for vertex in shape.vertices}
    counts = [len(value) for value in (shape.bodies, shape.shells, shape.faces, shape.edges, shape.vertices)]
    require(observed == {(*point, level) for point, level in product(outline, STATIONS)}
            and counts == [1, 1, 8, 18, 12],
            "strict reader changed the oriented L prism topology or coordinates")
    volume, area, centroid = ShellMeasures(shape)
    if measured is not None:
        pairs = ((volume * 1e-9, measured["volume_m3"]), (area * 1e-6, measured["area_m2"]),
                 *((observed * 1e-3, native)
                   for observed, native in zip(centroid, measured["com_m"], strict=True)))
        require(all(isclose(first, second, rel_tol=1e-12) for first, second in pairs),
                "signed neutral integration disagrees with the native observations")
    design = open_document(data, source_format=FORMAT, strict=True, include_brep=False)
    design_body, = design.bodies
    require(design.brep is None and not design.brep_payloads
            and (design_body.id, design_body.final_feature_id) == (body.id, body.final_feature_id)
            and any(row.id == feature.id and row.name == feature.name for row in design.feature_timeline),
            "design-only read lost the imported feature or its design body")
    return {"topology": counts, "volume_mm3": volume, "area_mm2": area, "centroid_mm": centroid,
            "design_only_body_name": design_body.name, **binding}


def refuse_changes(document, varied, skewed, options):
    destination = BytesIO(b"caller content")
    destination.seek(3)
    measurement = options["solidworks_native_measurement"]
    spoofed = measurement | {"receipt": measurement["receipt"] | {"controls_healthy": False}}
    unsupported = "does not support the destination"
    unmatched = "no exact native measurement"

    def publish(doc, values=options, target=destination):
        return write_document(doc, target, destination_format=FORMAT, values=values)

    refusals = {
        "no_receipt": refuse(lambda: publish(document, {"final_destination": LOCATOR}),
                             ValueError, "requires an offline native measurement"),
        "changed_receipt": refuse(lambda: publish(document, options | {
            "solidworks_native_measurement": spoofed}), ValueError, "requires its exact controlled native receipt"),
        "varied_section": refuse(lambda: publish(varied), ValueError, unmatched),
        "changed_epoch": refuse(lambda: publish(document, options | {
            "solidworks_native_measurement": measurement | {"written_at": EPOCH + 1}}), ValueError, unmatched),
        "changed_locator": refuse(lambda: publish(document, options | {
            "final_destination": LOCATOR.replace("Candidates", "Other")}), ValueError, unmatched),
        "different_receipt_slot": refuse(lambda: publish(document, options | {
            "final_destination": LOCATOR.replace("ConcaveOwned", "ConcaveBare")}), ValueError, unmatched),
        "oblique_boundary": refuse(lambda: publish(skewed), NotFoundError, unsupported),
        "extra_metadata": refuse(lambda: publish(replace(document, metadata={"unmodeled": True})),
                                 NotFoundError, unsupported),
        "nonempty_registry_sink": refuse(lambda: publish(document), ValueError, "standalone"),
        "nonempty_direct_sink": refuse(lambda: SldprtWriter().write(
            document, destination, WriteOptions(values=options)), ValueError, "standalone"),
    }
    require(destination.tell() == 3 and destination.getvalue() == b"caller content",
            "a refusal modified its caller's sink")
    return refusals


def refuse_paths(document, options):
    with TemporaryDirectory(prefix="kit-concave-refuse-") as scratch:
        path = Path(scratch) / "ConcaveOwned.SLDPRT"
        path.write_bytes(b"retain prior output")
        refuse(lambda: SldprtWriter().write(document, path, WriteOptions(overwrite=True, values=options)),
               ValueError, "actual measured Windows destination")
        missing = path.parent / "new" / path.name
        refuse(lambda: write_document(document, missing, destination_format=FORMAT, values=options),
               ValueError, "actual measured Windows destination" if sys.platform != "win32"
               else "no exact native measurement")
        require(path.read_bytes() == b"retain prior output" and tuple(path.parent.iterdir()) == (path,),
                "a rejected path write changed its prior file or left a stage")


def check(coverage_only=False):
    for codec in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(codec)
    raw_receipt, reference = RECEIPT.read_bytes(), REFERENCE.read_bytes()
    require(sha256(raw_receipt).hexdigest() == RECEIPT_SHA, "native receipt changed")
    receipt = json.loads(raw_receipt)
    case = receipt["cases"]["ConcaveOwned"]
    expected = {"bytes": case["generated_bytes"], "sha256": case["native_input_sha256"]}
    require(fingerprint(reference) == expected, "exact measured comparison part changed")
    options = {"final_destination": LOCATOR,
               "solidworks_native_measurement": {"written_at": EPOCH, "receipt": receipt}}
    settings = WriteOptions(values=options)
    document = CadDocument.from_json(prism(OUTLINE, STATIONS).to_json())
    shifted = tuple((x + 5.5, y - 3.0) for x, y in OUTLINE)
    varied = prism(shifted, STATIONS)
    skewed = prism((OUTLINE[0], OUTLINE[1], (36, -3), *OUTLINE[3:]), STATIONS)
    GetDocumentCaps(document)
    result = {"passed": True, "archive": expected, "native_receipt_sha256": RECEIPT_SHA,
              "native_processes_started": 0, "heldout_cases": 0}
    with guard() as accesses:
        prepared = PrepareImport(document, BytesIO(), EPOCH, settings)
        exact = prepared.BytesValue == reference
        if coverage_only and not exact and "zlib-ng" in ZLIB_RUNTIME_VERSION:
            stream = BytesIO()
            refusal = refuse(lambda: write_document(document, stream, destination_format=FORMAT,
                                                     values=options),
                             ValueError, "no exact native measurement")
            require(stream.getvalue() == b"", "an unmeasured compressor output was published")
            result |= {"exact_publications": 0, "unmatched_compressor": ZLIB_RUNTIME_VERSION,
                       "distinct_compression_refused": refusal}
        else:
            require(exact and {name: fingerprint(data) for name, data in prepared.StreamsValue.items()}
                    == case["generated_streams"], "complete neutral output is not the archived native input")
            staged = BytesIO()
            direct = BytesIO()
            for public_result in (
                write_document(document, staged, destination_format=FORMAT, values=options),
                SldprtWriter().write(document, direct, settings),
            ):
                assert_result(public_result)
                measured = public_result.metadata["solidworks_native_measurement"]
                require(measured["generated_sha256"] == case["native_input_sha256"]
                        and [measured["rebuild_record_sha256"], measured["reopen_record_sha256"]]
                        == case["native_observation_hashes"], "publisher cited a different native case")
            require(prepared.BytesValue == staged.getvalue() == direct.getvalue(),
                    "normal SDK and direct archive bytes differ")
            result |= {"exact_publications": 2, "exact_streams": len(prepared.StreamsValue),
                       "refusals": refuse_changes(document, varied, skewed, options)}
        variant = PrepareImport(varied, BytesIO(), EPOCH, settings)
        require(variant.BytesValue != prepared.BytesValue, "writer ignored independent model placement")
    result["runtime_external_events"] = len(accesses)
    result["readback"] = read_back(prepared.BytesValue, case["geometry"])
    result["varied_readback"] = read_back(variant.BytesValue, None, shifted)
    refuse_paths(document, options)
    if not exact:
        check_compression(prepared.BytesValue, reference)
    return result | {"rejected_paths_preserved": True}


if __name__ == "__main__":
    parser = ArgumentParser(description="Verify the measured concave solid without a CAD runtime")
    parser.add_argument("--remote-coverage", action="store_true")
    args = parser.parse_args()
    print(json.dumps(check(args.remote_coverage), indent=2, sort_keys=True, allow_nan=False))
