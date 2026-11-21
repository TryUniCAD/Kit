from argparse import ArgumentParser
from copy import deepcopy
from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


TOOL = Path(__file__).resolve()
sys.path.insert(0, str(TOOL.parent))
from PlanarRegistryBuild import ROOT, file_sha, load, require, write
from ProvePlanarVisualComposition import (
    IDENTITY, LABELS, SHAPE_REFUSAL, VISUALS, bind_sdk, canonical, change_set,
    independently_authored, run, source_request,
)


BASE = "aa76928bfd03d3bcff777f27cbf91237caa13c92"
PRIOR_RENDERLESS = "fffb454a8b9b26331b7bb66e53c27e41422795bd4b314d2a5ff67c4e0039c8a0"
MATERIAL_DLL = "af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735"
MODEL_DLL = "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"
SD_DLL = "ev_6bbb498331554d86758f2e64322d54623e287a1a5108ba1b81b04c8a2261ae5a"
DEFINITION = "Contents/Definition"
CONFIG = "Contents/Config-0"
CMGR = "Contents/CMgr"


def failure(call, error):
    try:
        call()
    except (ValueError, TypeError) as caught:
        require(str(caught) == error, "source owner failed at a different guard: " + str(caught))
        return error
    raise ValueError("unsupported source owner was admitted")


def stable(out):
    return {key: value for key, value in out.items() if key != "pid"}


def run_pair(request):
    first, second = (run(ROOT, request) for _ in range(2))
    require(stable(first) == stable(second)
            and first["pid"] != second["pid"]
            and first["runtime_input_reads"] == second["runtime_input_reads"] == 0,
            "independent renderer workers failed deterministic guarded composition")
    return first, (first["pid"], second["pid"])


def input_faults(request):
    cases = {
        "crossed-render-cursor": "planar child visual store requires its actual independent appearance allocator",
        "aliased-shader": "part self visibility lost the actual live renderer owners",
        "bad-material-resource": "part rendering requires an explicit ordinary stock color resource",
        "wrong-template": "part rendering requires the opaque nontextured basic shader",
        "no-space-for-events": "part rendering needs two nonwrapping appearance allocation events",
        "malformed-bom-marker": "empty BOM presence requires an explicit boolean",
        "asset-not-absolute": "part rendering requires an absolute Windows data-directory alias",
    }
    negatives = {}
    for name, expected in cases.items():
        bad = deepcopy(request)
        look = bad["self_appearance"]["appearance"]
        if name in ("crossed-render-cursor", "aliased-shader"):
            bad["fault"] = name
        elif name == "bad-material-resource":
            look["ResourceName"] = r"graphics\materials\other.p2m"
        elif name == "wrong-template":
            look["ShaderValue"]["ShaderType"] = "texture"
        elif name == "no-space-for-events":
            look["StartAppearanceId"] = (1 << 64) - 2
        elif name == "malformed-bom-marker":
            look["EmptyBomOnWire"] = 1
        elif name == "asset-not-absolute":
            look["DataDirectory"] = "data"
        negatives[name] = run(ROOT, bad, error=expected)
    return negatives


def source_faults(archive, registry):
    from PlanarRendererInput import observe_looks, project_look

    looks, state, _ = observe_looks(archive, registry)
    result = {}
    first = deepcopy(looks)
    first[0]["f88"]["f12c"] = first[1]["f88"]["f12c"] = first[2]["f88"]["f12c"] = 0.25
    result["wrong-derived-reflectance"] = failure(
        lambda: project_look(*first, state), "unrepresented renderer source field model.f88.f12c"
    )
    crossed = deepcopy(looks)
    crossed[1]["f88"]["f60"] = 0.125
    result["crossed-selected-config"] = failure(
        lambda: project_look(*crossed, state), "renderer source alters its active selected configuration appearance"
    )
    broken = deepcopy(looks)
    broken[2]["f20"]["f90"]["f68"] = broken[0]["f20"]["f90"]["f68"]
    result["crossed-installation-alias"] = failure(
        lambda: project_look(*broken, state), "renderer source requires a consistent live and detached resource alias"
    )
    stale = replace(state, AppearanceValue=replace(state.AppearanceValue, NextAppearanceId=state.AppearanceValue.NextAppearanceId - 1))
    result["stale-definition-allocator"] = failure(
        lambda: project_look(*looks, stale), "renderer source has a conflicting independent Definition allocator"
    )
    return result


def effective_input():
    from PlanarRendererInput import RESOURCE
    from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.BasicPbrInput import BasicPbrInput
    from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.ClassicLook import ClassicLook
    from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.PartLookInput import PartLookInput

    request = independently_authored()
    appearance = PartLookInput(
        r"C:\RenderProfiles\data", RESOURCE, (1 << 32) + (1 << 31) - 2, False,
        (17, 203, 83), (21, 41, 61), "", 0.29,
        ClassicLook("defaultplastic", 3, 1, 0.23, 0.625, 0.007, 0.013, False, False),
        BasicPbrInput("2025x", "basic", (37, 89, 132), (70, 43, 128), (19, 31, 47), 0.25,
                      0.375, 0.77, 0.47, 1.5, 64.25, 1.4, False, True),
    )
    request["self_appearance"]["appearance"] = asdict(appearance)
    return request


def compare_independent():
    seed = effective_input()
    builder, processes = run_pair(seed)
    request = deepcopy(seed)
    request["self_appearance"]["appearance"]["ShaderValue"]["RefractionIndex"] = 3.0
    ior, ior_pids = run_pair(request)
    request = deepcopy(seed)
    request["self_appearance"]["appearance"]["DataDirectory"] = r"D:\AlternateMount\data"
    moved, moved_pids = run_pair(request)

    require(builder["parent"] == ior["parent"] == moved["parent"]
            and builder["labels"] == ior["labels"] == moved["labels"]
            and builder["occurrences"] == ior["occurrences"] == moved["occurrences"],
            "authored rendering altered the neutral assembly roles")
    require(change_set(builder["child"]["streams"], ior["child"]["streams"]) == [CMGR, CONFIG, VISUALS]
            and change_set(builder["child"]["streams"], moved["child"]["streams"]) == [CMGR, CONFIG]
            and ior["renderer"]["reflectance"] == 0.25 and ior["renderer"]["refraction_index"] == 3.0
            and builder["renderer"]["holder_asset"] == moved["renderer"]["holder_asset"]
            and builder["renderer"]["live_asset"] != moved["renderer"]["live_asset"],
            "independent render scalar or resource alias did not affect only its actual owners")
    cursor = seed["self_appearance"]["appearance"]["StartAppearanceId"]
    require([builder["renderer"][key] for key in (
        "holder_id", "model_and_configuration_id", "definition_next_appearance_id"
    )] == [cursor, cursor + 1, cursor + 2] and cursor + 2 == 0x180000000
            and not builder["renderer"]["empty_bom_present"],
            "independent signed-half crossing or empty BOM ownership changed")
    return {name: stable(out) for name, out in (("base", builder), ("index_changed", ior), ("locator_changed", moved))}, [
        *processes, *ior_pids, *moved_pids]


def control_assertion(old, current):
    require(all(old[key] == current[key] for key in ("parent", "child", "occurrences", "ordered_mates", "mate_ids", "labels")),
            "the preexisting constructor-only path changed its complete output")


def prove(disclosed):
    bind_sdk(ROOT)
    from PlanarRendererInput import request_look
    from ProvePlanarMateGroup import checked, controls, source_cases
    from para.concentric.ProveVisualStateStore import registry
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    measures = ROOT / "re/solidworks/measurements/2026"
    identity = load(measures / "SdkPlanarAssemblyIdentity01.json", IDENTITY)["cases"]
    prior = load(measures / "SdkPlanarPriorSourceAdmission01.json", LABELS)["cases"]
    no_renderer = load(measures / "SdkPlanarVisualComposition01.json", PRIOR_RENDERLESS)["cases"]
    observer = registry()
    cases, processes = {}, []
    for row in source_cases(disclosed):
        case = row["case"]
        request, read_pid, source = source_request(row, prior[case], identity[case])
        child = SldprtArchive.from_bytes(checked(Path(row["child"]), row["child_sha256"]))
        authored, actual = request_look(child, observer)
        before = run(ROOT, request)
        control_assertion(no_renderer[case]["generated"], before)
        request["self_appearance"]["appearance"] = authored
        fresh, workers = run_pair(request)
        require(fresh["parent"] == before["parent"] and fresh["occurrences"] == before["occurrences"]
                and fresh["ordered_mates"] == before["ordered_mates"] and fresh["mate_ids"] == before["mate_ids"]
                and fresh["labels"] == before["labels"] and fresh["parent_store"] == before["parent_store"]
                and change_set(before["child"]["streams"], fresh["child"]["streams"]) == [
                    CMGR, CONFIG, DEFINITION, VISUALS],
                "renderer computation changed an unrelated modeled owner")
        cursor = actual["roles"]["definition_next_appearance_id"]
        require(fresh["renderer"]["holder_id"] == cursor and fresh["renderer"]["model_and_configuration_id"] == cursor + 1
                and fresh["renderer"]["definition_next_appearance_id"] == cursor + 2
                and fresh["renderer"]["empty_bom_present"] and actual["store"]["physical_density_parameter"] == [1000.0, 0]
                and fresh["renderer"]["physical_density_parameter"] is None
                and source["whole_source_guard"] == repr(ValueError(SHAPE_REFUSAL)),
                "renderer proof crossed its independent physical or whole-source bound")
        cases[case] = {"source": actual, "packed_author_input_sha256": sha256(canonical(authored)).hexdigest(),
                       "source_locks": source["source_locks"],
                       "source_refusals": source_faults(child, observer), "fresh_part": fresh["child"],
                       "fresh_renderer": fresh["renderer"], "fresh_parent": fresh["parent"], "legacy_same_bytes": True,
                       "source_ordered_datum_and_clock_boundary": no_renderer[case]["feature_id_and_clock_mapping"],
                       "whole_source_guard": SHAPE_REFUSAL}
        processes.extend((read_pid, before["pid"], *workers))

    physical = {}
    for row in controls(disclosed)[:2]:
        a = SldprtArchive.from_bytes(checked(Path(row["child"]), row["child_sha256"]))
        graph = ReadNativeLink(a, 0)
        config_fields = ReadCmgrMut(a.require(CMGR), 19000).RootValue.FieldsValue["f360"].FieldsValue
        mat = graph.ConfigValue.RootValue.FieldsValue["f1420"]
        physical[row["case"]] = {"source_sha256": row["child_sha256"], "config_density": config_fields["fc50"],
            "density_owner": None if mat is None else [mat.ClassValue.NameValue, mat.FieldsValue["f08"].ClassValue.NameValue,
                mat.FieldsValue["f08"].FieldsValue["f58"], mat.FieldsValue["f08"].FieldsValue["f68"]]}
    independent, varied_pids = compare_independent()
    processes.extend(varied_pids)
    require(len(set(processes)) == len(processes), "renderer workers lacked fresh process isolation")
    negatives = input_faults(effective_input())
    files = subprocess.check_output(("git", "diff", "--name-only", BASE), cwd=ROOT).decode().splitlines()
    files += subprocess.check_output(("git", "ls-files", "--others", "--exclude-standard", "--", "src", "re/tooling"), cwd=ROOT).decode().splitlines()
    return {"schema": "kit.sw2026.planar-renderer.v1", "base": BASE, "previous_receipt": PRIOR_RENDERLESS,
            "inputs": {name: file_sha(ROOT / name) for name in sorted(set(files)) if name.endswith(".py")},
            "module_evidence": {"sldmfcu_sha256": MATERIAL_DLL, "sldmodu_sha256": MODEL_DLL, "rea_resource_id": SD_DLL},
            "cases": cases, "physical_control": physical, "independent": independent,
            "guarded_renderer_writes": len(processes) - 2, "strict_source_reads": 2, "guarded_writer_refusals": negatives,
            "runtime_reads": 0, "native_processes": 0, "written_cad_files": 0,
            "public_write_qualified": False, "whole_source_admitted": False, "new_heldout_credit": 0, "passed": True}


def main():
    parser = ArgumentParser()
    parser.add_argument("--disclosed", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    disclosed, output = args.disclosed.resolve(strict=True), args.output.resolve()
    require(not output.exists() and not output.is_relative_to(disclosed) and not output.is_relative_to(ROOT),
            "use an unused private receipt path outside both the repository and source")
    print(write(output, prove(disclosed)))


if __name__ == "__main__":
    main()
