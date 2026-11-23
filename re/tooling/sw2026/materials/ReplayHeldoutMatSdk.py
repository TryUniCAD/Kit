from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(HERE)]

from PrepareMaterialHeldout import neutral, require, validate
from convert import write_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Presentation.MakeModelVisual import KModelTint
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from convert.adapters.solidworks.Core.Preparation.Materials.PlanMatPart import KMatAnchor, KMatCatalog
from convert.adapters.solidworks.Core.Preparation.Materials.PrepMatPart import PrepMatPart
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.materials.MaterialRecord import MaterialRecord
from interchange.serialization.JsonCodec import DumpJson, LoadJson


SLOTS = ("Candidate01", "Candidate02")
GENERATION = "c6b72fc0ab57e45d028cd9704fd1096c5ccc53d3207575dbb589924461491821"
PLAN = "466aa7a7c7cb5256fb086c1f57917d43444dcbe17743fb5437625e3837f986e3"
ORIGIN = "1244bee1cabdf468380e761bc99e2c623426ed6c595f73cf402b01330416473e"
NATIVE = "e80eb2c50cbca5c8ac5c0927a58eeceb02ca391a3ba86cec6c124cd603e1799e"
MANAGER = "Contents/CMgr"
FORMAT = "solidworks.sldprt"
MEASUREMENT = "solidworks_native_measurement"
PUBLIC_AUTHORITY = ROOT / "re/solidworks/measurements/2026/AssignedMaterialPhysicalAuthority01.json"


def read(root, relative, fingerprint):
    path = root / relative
    require(path.resolve(strict=True) == path and not path.is_symlink(), "indirect protected metadata")
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == fingerprint, "protected metadata fingerprint differs")
    return json.loads(raw)


def process(row):
    identity = row.get("identity") or row["oracle_identity"]
    require(identity["sha256"] == KOraclePart["sha256"] and identity["file_version"] == KOraclePart["build"]
            and identity["version_matches"] is True, "native phase used a different SOLIDWORKS executable")
    return identity["process_id"], identity["process_creation_filetime"]


def native_join(root):
    require(sys.platform == "win32" and root == Path(r"C:\KitSealedMaterialEvaluation01")
            and root.resolve(strict=True) == root, "material custody requires its original guest directory")
    generation = read(root, "GenerationFreeze.json", GENERATION)
    plan = read(root, "LifecyclePlan.json", PLAN)
    proofs = read(root, "Inspection03/OriginProof.json", ORIGIN)
    measured = read(root, "Inspection03/Result.json", NATIVE)
    require(plan["generation_sha256"] == GENERATION and plan["source_controls_healthy"] is True
            and generation["guarded_workers"] == 6
            and tuple(row["label"] for row in generation["cases"]) == SLOTS
            and tuple(measured["cases"]) == SLOTS, "native plans and stored generation differ")
    controls = {role: measured[role] for role in ("before", "after")}
    require(all(row["passed"] is True for row in controls.values()), "native controls did not pass")
    lifetimes = {process(row) for row in controls.values()}
    cases = []
    for selection, family in zip(generation["cases"], ("corner", "center"), strict=True):
        slot = selection["label"]
        observations = measured["cases"][slot]
        require(set(observations) == {"edit", "reopen"}
                and len(observations["edit"]["states"]) == 4 and len(observations["reopen"]["states"]) == 2
                and all(row["passed"] is True and row["open_errors_warnings"] == [0, 0] for row in observations.values())
                and all(state["native_proxy_verified"] is True and state["locked_source_comparison"] is True
                        for row in observations.values() for state in row["states"].values())
                and proofs[slot]["artifact_sha256"] == selection["artifact_sha256"]
                and proofs[slot]["typed_origin_chain"] is True and selection["family"] == family,
                "candidate did not pass its complete assigned-material lifecycle")
        lifetimes.update(process(row) for row in observations.values())
        cases.append({"anchor": family, "archive_sha256": selection["artifact_sha256"], "native_states": 6,
                      "numeric_checks": sum(row["numeric_checks"] for row in observations.values()),
                      "native_edit_sha256": observations["edit"]["record_sha256"],
                      "native_reopen_sha256": observations["reopen"]["record_sha256"]})
    numeric_checks = sum(row["numeric_checks"] for row in cases)
    require(len(lifetimes) == 6 and numeric_checks == 120, "native lifetimes or comparison counts differ")
    return generation, {
        "schema": "kit.sw2026.assigned-material-physical-authority.v1",
        "oracle_build": KOraclePart["build"], "oracle_sha256": KOraclePart["sha256"],
        "generation_sha256": GENERATION, "lifecycle_plan_sha256": PLAN, "origin_proof_sha256": ORIGIN,
        "native_result_sha256": NATIVE, "native_processes": len(lifetimes), "native_states": 12,
        "native_numeric_checks": numeric_checks, "cases": cases,
        "controls": {role: row["record_sha256"] for role, row in controls.items()},
    }


def guard():
    for name in ("document.Models.DocumentProvenance", "document.Validation.DocumentValidate",
                 "document.Validation.DocumentAssemblyValidate", "document.Validation.DocumentFeatureValidate",
                 "document.Validation.DocumentReferenceValidate", "document.Behavior.DocumentIo",
                 "brep.Validation.BrepValidate"):
        import_module("interchange." + name)
    for encoding in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(encoding)
    denied = []

    def audit(event, _args):
        if event in ("open", "os.listdir", "os.scandir", "os.exec", "os.fork", "os.forkpty",
                     "os.system", "os.posix_spawn", "ctypes.dlopen") or event.startswith(("socket.", "subprocess.")):
            denied.append(event)
            raise PermissionError("guarded material generation attempted external input")

    sys.addaudithook(audit)
    return denied


def inspect(candidate, material, catalog):
    archive = SldprtArchive.FromBytes(candidate.BytesValue)
    require(archive.streams == candidate.StreamsValue, "container and generated streams differ")
    link = ReadNativeLink(archive, 0)
    part = link.ConfigValue
    resolved = link.ResolvedValue
    manager = ReadCmgrMut(archive.require(MANAGER), 19000)
    cfg = manager.RootValue.FieldsValue
    require(cfg["f360"] is cfg["f368"] is cfg["f370"]["items"][0]["o"], "assigned material lost its configuration")
    fields = cfg["f360"].FieldsValue
    require(part.RootValue.FieldsValue["f1420"].FieldsValue["f08"].FieldsValue["f58"] == fields["fc50"] == material.Density
            and fields["f78"].FieldsValue["f20"]["f20"] == catalog + "|" + material.name,
            "generated material owners differ from the requested assignment")
    config_bytes, cfg = WriteConfigMut(part.RootValue, 19000, part.HeaderValue)
    resolved_bytes, write = WriteResolMut(resolved.RootsValue, resolved.ExtraFields, 19000, cfg.MapValue, resolved.ContextValue)
    replays = {link.ConfigName: config_bytes, link.StreamName: resolved_bytes, MANAGER: WriteCmgrMut(manager.RootValue, 19000)}
    require(all(payload == archive.require(name) for name, payload in replays.items())
            and write.MapValue == resolved.MapValue and cfg.MapValue == part.MapValue,
            "linked material streams fail typed replay")
    return sorted(replays)


def write_registry(document, sink, options):
    return write_document(document, sink, destination_format=FORMAT, allow_carrier=False, values=options)


def write_direct(document, sink, options):
    return SldprtWriter().write(document, sink, WriteOptions(values=options))


def write_adapter(document, sink, options):
    return SldprtAdapter().write(document, sink, WriteOptions(values=options))


def verify_public(document, restored, candidate, locator, epoch, receipt):
    options = {"final_destination": str(locator), MEASUREMENT: {"written_at": epoch, "receipt": {"native_report": receipt}}}
    alternate = replace(document.materials[0], Density=document.materials[0].Density * 1.25)
    mutated_material = replace(document, materials=(alternate,))
    unowned_material = replace(document, bodies=(replace(document.bodies[0], material_id=None),))
    unqualified_material = replace(document, metadata={"name": document.metadata["name"]})
    wrong_epoch = {**options, MEASUREMENT: {**options[MEASUREMENT], "written_at": epoch + 1}}
    wrong_report = {**options, MEASUREMENT: {**options[MEASUREMENT], "receipt": {"native_report": receipt + " "}}}
    variants = ((mutated_material, options), (unowned_material, options), (unqualified_material, options),
                (document, wrong_epoch), (document, wrong_report), (document, {"final_destination": str(locator)}))
    results = {}
    for write in (write_registry, write_direct, write_adapter):
        for model in (document, restored):
            sink = BytesIO()
            result = write(model, sink, options)
            require(sink.getvalue() == candidate.BytesValue and result.vendor_loadable and result.application_usable
                    and result.metadata[MEASUREMENT]["generated_sha256"] == sha256(candidate.BytesValue).hexdigest(),
                    "public writer emitted an unmeasured assigned-material archive")
        for invalid, settings in variants:
            sink = BytesIO()
            try:
                write(invalid, sink, settings)
            except (ValueError, NotFoundError):
                require(not sink.getvalue() and sink.tell() == 0, "refused material altered its destination")
            else:
                raise ValueError("public writer accepted unmeasured material or evidence")
        results[write.__name__] = {"exact_archives": 2, "prewrite_refusals": len(variants)}
    return results


def replay(root, slot, publication):
    generation, authority = native_join(root)
    index = SLOTS.index(slot)
    selection, measured = generation["cases"][index], authority["cases"][index]
    request = read(root, f"Generation/{slot}/Request.json", selection["request_sha256"])
    case, catalog, locator = validate(request)
    catalog, name, density = catalog[case["first_material_key"]]
    require(case["kind"] == measured["anchor"], "neutral request has the wrong measured anchor")
    receipt = PUBLIC_AUTHORITY.read_bytes().decode("utf-8") if publication else None
    if receipt is not None:
        require(json.loads(receipt) == authority, "published material authority differs from the original observations")
    denied = guard()
    tint = tuple(((KModelTint >> shift) & 255) / 255 for shift in (0, 8, 16)) + (1.0,)
    material = MaterialRecord("material/assigned-part", name, density, tint)
    document = neutral(case, locator, material)
    document = replace(document, bodies=(replace(document.bodies[0], material_id=material.id),),
                       metadata={**document.metadata, KMatCatalog: catalog, KMatAnchor: case["kind"]})
    restored = LoadJson(DumpJson(document))
    require(restored == document, "neutral assignment changed during JSON round trip")
    options = WriteOptions(values={"final_destination": str(locator)})
    epoch = request["target"]["saved_at"]
    result = PrepMatPart(document, BytesIO(), epoch, options)
    repeated = PrepMatPart(restored, BytesIO(), epoch, options)
    digest = sha256(result.BytesValue).hexdigest()
    require(result.BytesValue == repeated.BytesValue and digest == measured["archive_sha256"],
            "model does not regenerate the archive used in the native lifecycle")
    replays = inspect(result, material, catalog)
    public = verify_public(document, restored, result, locator, epoch, receipt) if receipt is not None else {}
    require(not denied, "native material composition attempted an external source")
    return {"case": slot, "anchor": measured["anchor"], "archive_sha256": digest, "bytes": len(result.BytesValue),
            "streams": len(result.StreamsValue), "typed_stream_replays": replays,
            "runtime_reads": len(denied), "native_processes_started": 0, "publication": public}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--slot", choices=SLOTS)
    parser.add_argument("--publication", action="store_true")
    args = parser.parse_args()
    try:
        result = replay(args.root, args.slot, args.publication) if args.slot else native_join(args.root)[1]
    except Exception as exc:
        raise SystemExit(f"material proof refused ({type(exc).__name__})") from None
    print(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False))
