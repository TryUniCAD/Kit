import argparse
import base64
from dataclasses import asdict, replace
from hashlib import sha256
from pathlib import Path
import codecs
import json
import subprocess
import sys


REPO = Path(__file__).resolve().parents[5]
SW2026 = REPO / "re/tooling/sw2026"
sys.path[:0] = [str(REPO), str(REPO / "src"), str(SW2026), str(SW2026 / "serial")]

from CheckConcentricSourceBrep import map_source_endpoints
from convert import open_document
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Archive.Construction.Assembly.MakeAsmBase import MakeAsmBase
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.AsmKeyNodes import AsmKeyNodes
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName, ReadRows, RequireNode, RequireRecord
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import ReadAsmModel
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadLightInput import ReadLightInput
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import ReadChildren
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.serialization.Deserialize import FromData
from para.concentric.ProjectConcentricRadialIntent import light_values, read_intents
from para.concentric.ProveConcentricSourceBrep import D01_LOCKED, RADIAL_LOCKED, checked, json_digest, require, source_case
from para.concentric.ProveSignedConcentricWriter import emit_parts, inventory_receipt, neutral_d01, plan_bundle, source_inventory, verify_legacy, verify_parts


BASELINE = "a794b0b3adfbf619ad00bd177203eefddda571d5"
SEED = "e5e005dc738ad379f0485accc78d7f72002cccdc1b14186ea43ed82e4f444fe3"
EPOCH = 1816312041
ROOT_NAME = "ConcentricParentLightProof"
TOOL_FILE = "re/tooling/sw2026/para/concentric/ProveConcentricParentLights.py"
CORE_PATHS = (
    "Assembly/AssemblySysIn.py", "Assembly/System/MakeAsmSysMut.py",
    "Assembly/Xml/AsmKeyNodes.py", "Assembly/Xml/AsmXmlRoles.py", "Assembly/Xml/MakeAsmKeys.py",
    "NestedAssemblies/MakeNestedKeys.py",
)


def digest(data):
    return sha256(data).hexdigest()


def read_scene(link, *, empty=False):
    root = RequireNode(link.ConfigValue.RootValue, "moAssembly_c")
    resolved = link.ResolvedValue
    require(link.ConfigName == "Contents/Config-0" and all(
        row.get("completed") and not row.get("missing_schemas") and not row.get("provisional_schemas")
        for row in (link.ConfigValue.ReportValue, resolved.ReportValue)
    ), "actual current configuration and resolved graph must be complete")
    environment = RequireNode(root.FieldsValue.get("f1e0"), "moEnvFolder_c")
    require(tuple(row for row in resolved.RootsValue if row.ClassValue.NameValue == "moEnvFolder_c")
            == (environment,) and sum(row is environment for row in resolved.RootsValue) == 1,
            "the actual configuration environment is not its unique resolved root")
    fields = RequireRecord(environment.FieldsValue.get("f60"))
    listing = RequireRecord(fields.get("list"))
    require(set(fields) == {"list", "tail"} and fields["tail"] == 0 and set(listing) == {"n", "items"}
            and all(set(row) == {"o"} for row in ReadRows(listing["items"])),
            "source environment contains unsupported list or item state")
    members = ReadChildren(environment)
    require(all(sum(entry.EntryValue is row for entry in resolved.MapValue.EntriesValue) == 1
                for row in (environment, *members))
            and not any(member is row for member in members for row in resolved.RootsValue),
            "environment members must be unique attached objects without flat resolved duplicates")
    lights = tuple(ReadLightInput(row) for row in members)
    expected_kinds = () if empty else ("ambient", "directional", "directional", "directional")
    require(tuple(row.KindValue for row in lights) == expected_kinds
            and len({row.NameValue for row in lights}) == len(lights),
            "source presentation is outside the bounded ordered four-light profile")
    return environment, members, lights


def public_light_rows(document, members, lights):
    rows = {row.attributes.get("native_object_id"): row for row in document.feature_timeline}
    require(len(rows) == len(document.feature_timeline), "public keywords have repeated feature identities")
    actual = []
    for member, light in zip(members, lights, strict=True):
        ident = FieldInt(member.FieldsValue, "f08")
        row = rows[ident]
        role = "Ambient" if light.KindValue == "ambient" else "Directional"
        require(row.name == light.NameValue and row.attributes["native_type"] == role
                and row.attributes["xml_tag"] == "Feature", "normal assembly read lost an actual light keyword")
        actual.append((ident, row.name, role))
    return actual


def disclose(role, folder, file_names, hashes):
    document, raw, shape = source_case(folder, *file_names, hashes)
    archive = SldprtArchive.from_bytes(raw)
    environment, members, lights = read_scene(ReadNativeLink(archive, 0))
    return document, raw, shape, ReadNodeName(environment), tuple(light_values(row) for row in lights), {
        "case": role, "parent_sha256": hashes[0], "child_sha256": hashes[1],
        "environment_id": FieldInt(environment.FieldsValue, "f08"), "environment_name": ReadNodeName(environment),
        "public_keyword_rows": public_light_rows(document, members, lights),
        "source_creation_instants": [asdict(row.CreatedValue) for row in lights],
        "original_parent_model_sha256": json_digest(document),
    }


def with_lights(bundle, caption, lights):
    attachment, intent, settings, poses = bundle
    system = settings.SystemValue
    folders = tuple((role, caption if role == "moEnvFolder_c" else name) for role, name in system.FolderNames)
    updated = replace(settings, SystemValue=replace(system, FolderNames=folders, LightValues=lights))
    return attachment, intent, updated, poses


def check_archive(payload, expected, *, empty=False):
    archive = SldprtArchive.from_bytes(payload)
    link = ReadNativeLink(archive, 0)
    env, members, lights = read_scene(link, empty=empty)
    require(lights == expected, "actual generated light intent differs")
    ids = [FieldInt(row.FieldsValue, "f08") for row in members]
    require(len(set(ids)) == len(ids) and all(member < FieldInt(link.ConfigValue.HeaderValue.FieldsValue, "f08") for member in ids),
            "lights must share the actual assembly persistent allocator and published header")
    return archive, env, members


def source_refusals(raw):
    cases = {}

    def foreign_environment(root, env):
        root.FieldsValue["f1e0"] = ArchiveNode(env.ClassValue, dict(env.FieldsValue))

    def duplicate_child(_root, env):
        rows = env.FieldsValue["f60"]["list"]["items"]
        rows[1] = rows[0]

    def foreign_class(_root, env):
        child = env.FieldsValue["f60"]["list"]["items"][0]
        child["o"].ClassValue = env.ClassValue

    def hidden_user_state(_root, env):
        child = ReadChildren(env)[1]
        child.FieldsValue["f35c"] = 1

    def extra_list_state(_root, env):
        env.FieldsValue["f60"]["tail"] = 1

    for mutate in (foreign_environment, duplicate_child, foreign_class, hidden_user_state, extra_list_state):
        link = ReadNativeLink(SldprtArchive.from_bytes(raw), 0)
        root = link.ConfigValue.RootValue
        mutate(root, root.FieldsValue["f1e0"])
        try:
            read_scene(link)
        except (ValueError, TypeError) as error:
            cases[mutate.__name__] = str(error)
        else:
            raise ValueError("source admitted unsupported change " + mutate.__name__)
    return cases


def writer_refusals(bundle, scene, lights):
    result = {}

    def duplicate_key():
        b = with_lights(bundle, scene, lights)
        state = MakeAsmBase(b[2])
        member = ReadChildren(state.RootValue.FieldsValue["f1e0"])[0]
        return AsmKeyNodes(state.RootValue, (*state.FeatureValues, member))

    def misdirected_environment_key():
        b = with_lights(bundle, scene, lights)
        state = MakeAsmBase(b[2])
        actual = state.RootValue.FieldsValue["f1e0"]
        state.RootValue.FieldsValue["f1e0"] = ArchiveNode(actual.ClassValue, dict(actual.FieldsValue))
        return AsmKeyNodes(state.RootValue, state.FeatureValues)

    def foreign_member_owner():
        b = with_lights(bundle, scene, lights)
        state = MakeAsmBase(b[2])
        member = ReadChildren(state.RootValue.FieldsValue["f1e0"])[0]
        member.FieldsValue["owner"] = state.RootValue
        return AsmKeyNodes(state.RootValue, state.FeatureValues)

    def foreign_member_class():
        b = with_lights(bundle, scene, lights)
        state = MakeAsmBase(b[2])
        actual = state.RootValue.FieldsValue["f1e0"]
        ReadChildren(actual)[0].ClassValue = actual.ClassValue
        return AsmKeyNodes(state.RootValue, state.FeatureValues)

    for name, action in {
        "untyped_input": lambda: with_lights(bundle, scene, ({"NameValue": "bad"},)),
        "duplicate_caption": lambda: with_lights(bundle, scene, (lights[0], lights[0])),
        "system_caption_collision": lambda: with_lights(bundle, scene, (replace(lights[0], NameValue="Origin"),)),
        "duplicate_flat_keyword": duplicate_key, "foreign_keyword_owner": misdirected_environment_key,
        "foreign_member_owner": foreign_member_owner, "foreign_member_class": foreign_member_class,
    }.items():
        try:
            action()
        except (ValueError, TypeError) as error:
            result[name] = str(error)
        else:
            raise ValueError("writer admitted unsupported change " + name)
    return result


def build(document, axes, scene, source_lights):
    GetDocumentCaps(ReadAsmModel(document).ChildDocument)
    for encoding in ("utf-16-le", "utf-16-be", "cp1252", "utf-8"):
        codecs.lookup(encoding)
    lights = read_intents(source_lights, EPOCH)
    changed = (*lights[:1], replace(lights[1], NameValue="Directional1 Host Discriminator"), *lights[2:])
    active = True
    denied = []

    def guard(event, _):
        if active and event in {"open", "subprocess.Popen", "os.system", "os.posix_spawn", "os.fork", "socket.connect"}:
            denied.append(event)
            raise RuntimeError("assembly presentation attempted runtime access: " + event)

    sys.addaudithook(guard)
    try:
        bundle = plan_bundle(document, EPOCH)
        explicit = with_lights(bundle, scene, lights)
        parent = emit_parts(explicit, axes)
        repeated = with_lights(plan_bundle(document, EPOCH), scene, lights)
        require(emit_parts(repeated, axes) == parent and explicit[0].file_bytes == repeated[0].file_bytes,
                "repeated parent light construction differs")
        proof = verify_parts(parent, explicit, axes)
        archive, env, nodes = check_archive(parent, lights)
        require(ReadNodeName(env) == scene, "actual generated environment caption differs")
        plain = emit_parts(bundle, axes)
        neutral_archive, _, _ = check_archive(plain, (), empty=True)
        changed_input = with_lights(bundle, scene, changed)
        contrast = emit_parts(changed_input, axes)
        contrast_archive, _, _ = check_archive(contrast, changed)
        delta = sorted(key for key in archive.streams if archive.require(key) != neutral_archive.require(key))
        config = "Contents/Config-0"
        require(len(archive.require(config)) > len(neutral_archive.require(config))
                and len(contrast_archive.require(config)) > len(archive.require(config)),
                "computed assembly scene stream lengths did not follow typed input")
        failures = writer_refusals(bundle, scene, lights)
    finally:
        active = False
    require(not denied, "assembly presentation used runtime inputs")
    return parent, bundle[0].file_bytes, nodes, lights, {
        "parent_sha256": digest(parent), "child_sha256": digest(bundle[0].file_bytes),
        "empty_environment_sha256": digest(plain), "contrast_parent_sha256": digest(contrast),
        "config_stream_bytes": {"empty": len(neutral_archive.require(config)), "source": len(archive.require(config)),
                                "longer_light_name": len(contrast_archive.require(config))},
        "changed_streams": delta, "mate_readback": proof, "writer_refusals": failures,
        "repeat_count": 2, "runtime_file_process_network_attempts": len(denied),
    }


def nested_regressions(before):
    from tests.Convert.Solidworks.Research.Construction.Nesting.MakeNestedCase import MakeNestedCase

    reports = []
    for mixed in (False, True):
        request = json.dumps(MakeNestedCase(mixed, r"C:\KitParentLightsNested"), sort_keys=True, allow_nan=False).encode()
        rows = []
        for root in (before, REPO):
            result = subprocess.run(
                [sys.executable, "-I", "-B", str(root / "re/tooling/sw2026/SdkNestedAssemblyProcess.py"), str(root)],
                input=request, capture_output=True, check=True, timeout=100,
            )
            output = json.loads(result.stdout)
            require(output["passed"] and output["runtime_input_file_reads"] == 0 and output["heldout_inputs_read"] == 0,
                    "nested default construction lost its guarded closure")
            output.pop("worker_pid")
            rows.append(output)
        require(rows[0] == rows[1], "empty-env nested output or receipt differs from the exact earlier revision")
        reports.append({"mixed": mixed, "input_sha256": digest(request),
                        "full_document_sha256": {name: digest(base64.b64decode(row["blob"], validate=True))
                                                 for name, row in rows[1]["documents"].items()},
                        "linked_reemissions": rows[1]["typed_stream_round_trips"], "identical_default_bytes": True})
    return reports


def main():
    parser = argparse.ArgumentParser(description="Prove disclosed D01 parent lighting and prior empty-environment output")
    parser.add_argument("disclosed_root", type=Path)
    parser.add_argument("prior_source_closure", type=Path)
    parser.add_argument("new_scratch", type=Path)
    args = parser.parse_args()
    output = args.new_scratch.resolve()
    output.mkdir()
    prior_closure = source_inventory(args.prior_source_closure)
    current_closure = source_inventory(REPO)
    deltas = {name for name in set(prior_closure) | set(current_closure)
              if prior_closure.get(name) != current_closure.get(name)}
    prefix = "src/convert/adapters/solidworks/Archive/Construction/"
    require(deltas == {TOOL_FILE, *(prefix + path for path in CORE_PATHS)}, "source scope differs from the expected isolated overlay")
    base = args.disclosed_root.resolve()
    d01 = base / "ConcentricMateSourcePacket02/Disclosed/D01"
    lock = json.loads(checked(d01 / "lock.json", "bdd8bf3782ccf01991a3ac402da2923f2d320728792fb8ccb500f73189e9f90b"))
    require(lock["source_locked"] and not lock["heldout_source_locked"], "D01 is the only explicit source lock")
    files = ("ConcentricD01AlignedFree.SLDASM", "ConcentricD01Child.SLDPRT")
    source = disclose("D01Source", d01 / "Native/Source", files, D01_LOCKED["Source"])
    edited = disclose("D01Edited", d01 / "Native/Edited", files, D01_LOCKED["Edited"])
    radial = disclose("RadialNativeSaved", base / "RadialConcentric01/Working",
                      ("RadialConcentricProbe.SLDASM", "DisclosedRadialSceneProbe.SLDPRT"), RADIAL_LOCKED["Working"])
    parent, raw, shape, scene, light_intent, _ = source
    require(all(row[3:5] == source[3:5] for row in (edited, radial)),
            "parent light intent changes across the pinned independent source and native-save contexts")
    axes_owner = map_source_endpoints(parent, raw, shape, shape)
    axes = tuple(row["local_axis"] for row in axes_owner)
    seed = FromData(json.loads(checked(REPO / "re/solidworks/inputs/ConcentricFeatureNeutral01.json", SEED)))
    neutral = neutral_d01(seed, parent, axes_owner, shape, ROOT_NAME)
    generated, child, members, lights, proof = build(neutral, axes, scene, light_intent)
    native_parent = output / (ROOT_NAME + ".SLDASM")
    native_parent.write_bytes(generated)
    (output / "D01SignedChild.SLDPRT").write_bytes(child)
    public = open_document(native_parent, strict=True, include_brep=False, include_tessellation=False)
    proof["normal_reader_keyword_rows"] = public_light_rows(public, members, lights)
    proof["normal_reader_feature_count"] = len(public.feature_timeline)
    require(public.metadata["solidworks.typed_mates_semantics"]["status"] == "unsupported",
            "pre-solve source mate admission unexpectedly changed")
    try:
        ReadAsmModel(parent)
    except ValueError as error:
        require(str(error) == "assembly root contains unprojected model content", "the whole-source guard changed")
        whole_source_refusal = str(error)
    else:
        raise ValueError("whole-source admission unexpectedly changed")
    source_errors = source_refusals(raw)
    flat = verify_legacy(args.prior_source_closure, output)
    nested = nested_regressions(args.prior_source_closure)
    for inputs, name_pair, case in ((d01 / "Native/Source", files, source), (d01 / "Native/Edited", files, edited),
                                    (base / "RadialConcentric01/Working",
                                     ("RadialConcentricProbe.SLDASM", "DisclosedRadialSceneProbe.SLDPRT"), radial)):
        immutable = case[-1]
        for filename, role in zip(name_pair, ("parent", "child"), strict=True):
            checked(inputs / filename, immutable[role + "_sha256"])
        require(json_digest(case[0]) == immutable["original_parent_model_sha256"],
                "the disclosed parent model changed during scene projection")
    require(source_inventory(args.prior_source_closure) == prior_closure and source_inventory(REPO) == current_closure,
            "frozen source bytes changed")
    report = {
        "schema": "kit.sw2026.disclosed-parent-light-projection.v1", "baseline": BASELINE, "passed": True,
        "source_closures": {"before": inventory_receipt(prior_closure), "after": inventory_receipt(current_closure)},
        "changed_sources_sha256": {name: current_closure[name] for name in sorted(deltas)},
        "disclosed_sources": [row[-1] for row in (source, edited, radial)],
        "parent_lighting_intent": light_intent, "source_refusals": source_errors, "emission": proof,
        "prior_default_flat": flat, "prior_default_nested": nested,
        "root_refusal": whole_source_refusal, "whole_source_admitted": False, "disclosed_inputs_unchanged": True,
        "native_processes_started": 0, "sealed_inputs_read": 0, "public_writer_enabled": False,
    }
    receipt = output / "ConcentricParentLights01.json"
    receipt.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(digest(receipt.read_bytes()))


if __name__ == "__main__":
    main()
