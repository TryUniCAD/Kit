from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from uuid import UUID

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ObserveAssemblyPresentationCaches import native_motion
from ProveD01AssemblyChronology import compose_streams
from ProveD01ParentDisplay import build_arguments
from ProveSdkAsmInformation import (
    KInfoXml, MEASUREMENTS, MODEL, MODEL_PIN, PRIOR, PRIOR_PIN,
    PROOF, PROOF_PIN, checked, fingerprint, generate, model_inputs, neutral_request,
    prepare_package, refuse, registry, require, source_cases, stream_diff, wire,
)
from InspectPartEnvironmentSource import Image

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Construction.Assembly.Metadata.Information.AsmInfoInput import AsmInfoInput
from convert.adapters.solidworks.Archive.Construction.Assembly.Metadata.Information.MakeAsmInfo import MakeAsmInfo
from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Motion.MakeMotionGraph import MakeMotionGraph
from convert.adapters.solidworks.Archive.Motion.MotionLayouts import KMotionLayouts, KMotionSchemas
from convert.adapters.solidworks.Archive.Motion.MotionStudy import KDefaultStudy, MotionStudy
from convert.adapters.solidworks.Archive.Motion.ReadMotionStudy import ReadMotionStudy
from convert.adapters.solidworks.Archive.Motion.WriteMotionBody import WriteMotionBody
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Archive.Strings.EncodeString import EncodeString
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive


BASE = "e0d4349f18711d5ba9a04171c8a4b84d6e6603db"
MOTION = "ThirdPty/Animator"
MOTION_RECEIPT = "AssemblyPresentationCaches01.json"
MOTION_PIN = "ba9b9c36f1693e27ec6bc23ae5e34aa7e074c462175a7334652f9c4a09a57f7c"
SDK_INFO = "SdkAssemblyInformation01.json"
SDK_INFO_PIN = "8706f3a7d47d30689bd58af6ac6a5e74fcefd61fc96da49e2a72987d516b7366"
MODULES = {
    "sldmodu.dll": "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e",
    "doccplu.dll": "ad0c266a966381defe9a68c11b76dc318acc6a9f6ac428d5aa253049df87ddd8",
    "sldasmu.dll": "05ab90ee7380335088505c47202137c63dbce18d7d516e7fd6703aee31d70390",
    "slduiu.dll": "025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7",
    "sldanimationengineu.dll": "a4c5dba900d108fbffc4922c69964dfdabc4d53e2916c99298fb29ebab6b6fa1",
}
FIELD_WINDOWS = {
    "study_initialization": (0x4CA57F10, 0x4CA584D4),
    "study_store": (0x4CA2735E, 0x4CA276A4),
    "owned_controller_store": (0x4CA4B422, 0x4CA4B491),
    "selected_holder_empty_branch": (0x4CA28BF8, 0x4CA28C1F),
    "manager_extension_count": (0x4CA29D31, 0x4CA29D5F),
}


def static_owners(directory):
    images = {name: Image(directory / name, pin) for name, pin in MODULES.items()}
    model = images["sldmodu.dll"]
    windows = native_motion(directory / "sldmodu.dll")["windows"]
    windows.update({key: {"start": hex(start), "end_exclusive": hex(end),
                          "sha256": fingerprint(model.read(start, end))}
                    for key, (start, end) in FIELD_WINDOWS.items()})
    imports = model.imports()
    require(imports["0x4cd34f60"]["name"] == "CoCreateGuid"
            and imports["0x4cd34f70"]["name"] == "StringFromGUID2"
            and int.from_bytes(model.read(0x4D2A68E8, 0x4D2A68F0), "little") == 0x4CA4B3F0
            and int.from_bytes(model.read(0x4CDB02E0, 0x4CDB02E8), "little") == 0x4CA28B70,
            "study identity or controller/holder dispatch differs")
    return {"module_sha256": MODULES, "study_windows": windows,
            "controller_serialize_va": "0x4ca4b3f0", "holder_serialize_va": "0x4ca28b70",
            "caption_publisher_traced": False}


def caption_list(names):
    return EncodeCount(len(names)) + b"".join(EncodeString(CStringValue(name, True)) for name in names)


def research_member(study):
    return WriteMotionBody(study) + caption_list((study.NameValue,))


def add_motion(streams, study):
    require(MOTION not in streams, "assembly motion already has an owner")
    return streams | {MOTION: research_member(study)}


def compare_sources(disclosures, properties, known):
    found = {}
    for label, path, pin in source_cases(disclosures, properties):
        archive = SldprtArchive.from_bytes(checked(path, pin))
        data = archive.require(MOTION)
        study = ReadMotionStudy(data)
        prefix = WriteMotionBody(study)
        identity = fingerprint(str(study.IdentityValue).upper().encode("ascii"))
        require(research_member(study) == data and len(prefix) == 308
                and len(data) == known[label]["animator"]["bytes"] == 342
                and known[label]["animator"]["study_identity_sha256"] == identity
                and known[label]["source_sha256"] == pin,
                "typed ordinary motion body or caption directory differs")
        found[label] = {"source_sha256": pin, "member_sha256": fingerprint(data), "body_bytes": len(prefix),
                        "caption_bytes": len(data) - len(prefix), "active_index": -1, "study_count": 1,
                        "uuid_digest": fingerprint(study.IdentityValue.bytes), "controller_self_reference": True}
    require(len(found) == 12 and all(found[f"D0{case}/Source"]["member_sha256"]
            == found[f"D0{case}/Edited"]["member_sha256"] for case in (1, 2, 3)),
            "paired source study identity changed")
    return found


def emit_graph(root):
    context = BodyContext(19000, KMotionLayouts, {}, KMotionSchemas)
    writer = BodyWriter(ArchiveMaps(1), context, WriteBodyMut)
    WriteNodeMut(writer, root)
    return EncodeScalar(19000, "u32") + bytes(writer.OutputValue)


def refusals(streams, study):
    body = WriteMotionBody(study)
    captions = caption_list((study.NameValue,))
    active = MakeMotionGraph(study)
    active.FieldsValue["f30"] = 0
    orphan = MakeMotionGraph(study)
    orphan.FieldsValue["studies"][0]["o"].FieldsValue["f2c8"]["f08"] = None
    return {
        "duplicate": refuse(lambda: add_motion(add_motion(streams, study), study), "already has an owner"),
        "active": refuse(lambda: ReadMotionStudy(emit_graph(active) + captions), "ordinary inactive study"),
        "orphan": refuse(lambda: ReadMotionStudy(emit_graph(orphan) + captions), "actual self owned study"),
        "foreign_caption": refuse(lambda: ReadMotionStudy(body + caption_list(("Foreign",))), "caption directory"),
        "extra_caption": refuse(lambda: ReadMotionStudy(body + caption_list((study.NameValue,) * 2)), "caption directory"),
        "unsupported_name": refuse(lambda: replace(study, NameValue="New study"), "ordinary default study"),
        "wrong_uuid_version": refuse(lambda: replace(study, IdentityValue=UUID(int=0)), "version four identity"),
    }


def worker(payload, pins):
    require(set(payload) == {"model", "identities"}, "motion worker requires only modeled assembly and study identities")
    model = payload["model"]
    request, documents, models, properties, _ = prepare_package(model["neutral"])
    reg = registry()
    earlier, child, observed, accesses = generate(model, pins[0])
    require(observed["parent_sha256"] == pins[1], "earlier complete model exchange changed")
    _, bundle = compose_streams(request["models"], request["chronology"], documents, models, reg)
    arguments = build_arguments(request["models"]["after"], documents[1], models[1])
    headers = bundle.HeaderValue, bundle.TopHeader
    information = MakeAsmInfo(bundle.StateValue, headers, arguments[1].OutputValue,
                              AsmInfoInput(properties.created_at, properties.save_actor, -480, "en-US"))
    before = SldprtArchive.from_bytes(earlier)
    streams = before.streams | {KInfoXml: information}
    base_bytes = BuildSldprt(streams, FormatVersion=4)
    base = SldprtArchive.from_bytes(base_bytes)
    require(fingerprint(base_bytes) == pins[2] and fingerprint(child) == pins[3]
            and len(base.streams) == 35 and MOTION not in base.streams,
            "the previous 35-stream D01 bundle changed")
    studies = tuple(MotionStudy(UUID(identity), KDefaultStudy) for identity in payload["identities"])
    require(len(studies) == len(set(studies)) == 2, "provide two independent authored motion identities")
    variants = []
    for study in studies:
        candidate = BuildSldprt(add_motion(base.streams, study), FormatVersion=4)
        container = SldprtArchive.from_bytes(candidate)
        body = container.require(MOTION)
        require(len(container.streams) == 36 and stream_diff(base, container) == {MOTION}
                and ReadMotionStudy(body) == study, "fresh motion graph changed an independent assembly member")
        variants.append({"parent_sha256": fingerprint(candidate), "member_sha256": fingerprint(body),
                         "member_bytes": len(body), "parent_stream_count": len(container.streams)})
    require(variants[0]["member_sha256"] != variants[1]["member_sha256"]
            and variants[0]["parent_sha256"] != variants[1]["parent_sha256"],
            "independent model identities did not change their generated archive")
    negatives = refusals(base.streams, studies[0])
    require(not accesses, "motion construction attempted external access")
    return {"unchanged_parent_sha256": pins[2], "unchanged_child_sha256": pins[3],
            "unchanged_parent_members": len(base.streams), "authored_variants": variants,
            "refusals": negatives, "runtime_external_accesses": len(accesses)}


def main():
    parser = ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--disclosures", type=Path)
    action.add_argument("--worker", nargs=4)
    parser.add_argument("--native-dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        sys.stdout.buffer.write(wire(worker(json.load(sys.stdin), args.worker)))
        return
    require(args.output is not None and args.native_dir is not None, "supply licensed module directory and unused receipt path")
    pins = {PRIOR: PRIOR_PIN, PROOF: PROOF_PIN, MODEL: MODEL_PIN, SDK_INFO: SDK_INFO_PIN, MOTION_RECEIPT: MOTION_PIN}
    receipts = {name: json.loads(checked(MEASUREMENTS / name, pin)) for name, pin in pins.items()}
    saved = compare_sources(args.disclosures, receipts[PROOF], receipts[MOTION_RECEIPT]["disclosed_sources"])
    neutral = neutral_request(args.disclosures, receipts[PROOF])
    identities = [str(UUID(bytes=sha256(name.encode("ascii")).digest()[:16], version=4))
                  for name in ("Kit independently authored motion study one", "Kit independently authored motion study two")]
    request = wire({"model": model_inputs(neutral, receipts[PRIOR]), "identities": identities})
    previous = receipts[MODEL]["generated"]
    present = receipts[SDK_INFO]["generated"]
    command = (sys.executable, "-I", "-B", str(HERE), "--worker", previous["prior_parent_sha256"],
               previous["parent_sha256"], present["parent_sha256"], present["child_sha256"])
    first, second = (subprocess.run(command, input=request, capture_output=True, timeout=120) for _ in range(2))
    require(first.returncode == second.returncode == 0 and first.stdout == second.stdout,
            (first.stderr + second.stderr).decode() or "independent motion workers differ")
    root = HERE.parents[5]
    files = (*sorted((root / "src/convert/adapters/solidworks/Archive/Motion").glob("*.py")), HERE)
    known = receipts[SDK_INFO]["source_controls"]
    require(set(saved) == set(known) and all(saved[name]["source_sha256"] == row["source_sha256"]
            for name, row in known.items()), "ordinary model scope differs from earlier disclosed assemblies")
    result = {"schema": "kit.sw2026.d01-ordinary-motion.v1", "base": BASE, "prior_receipts": pins,
              "native_static": static_owners(args.native_dir), "source_controls": saved,
              "generated": json.loads(first.stdout), "guarded_workers": 2, "request_sha256": fingerprint(request),
              "native_processes_started": 0, "heldout_inputs_read": 0, "native_qualified": False,
              "source_sha256": {str(path.relative_to(root)): fingerprint(path.read_bytes()) for path in files}}
    with args.output.open("xb") as output:
        output.write(wire(result))


if __name__ == "__main__":
    main()
