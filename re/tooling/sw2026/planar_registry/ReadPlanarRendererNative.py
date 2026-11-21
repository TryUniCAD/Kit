from argparse import ArgumentParser
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PlanarRegistryBuild import ROOT, bind, require
from PlanarRendererNativeSpec import exact


def refusal(call, kind, wanted):
    try:
        call()
    except kind as error:
        require(str(error) == wanted, "the ordinary reader or writer refused a different owner: " + str(error))
        return str(error)
    raise ValueError("an explicitly unqualified whole-document path admitted the renderer")


def projected_prediction(geometry):
    from SdkPlanarGroupPrediction import transform

    case = geometry["case"]
    return {**geometry["options"], "initial": {
        "body_count": len(case["placements"]),
        "fixed_flags": [index == case["fixed_occurrence"] for index in range(len(case["placements"]))],
        "occurrence_transforms": [transform(placement) for placement in case["placements"]],
        "mate_values_m": [mate.get("distance_m") for mate in case["mates"]],
    }}


def observe(row, mode, prediction, appearance, display, source_labels, reg):
    from PlanarRendererInput import confirm_look, differences, request_look
    from PlanarAssemblyIdentity import request_view
    from PlanarVisualOwners import parent_store, source_definition
    from ReadSdkPlanarGroupNative import audit, compare
    from RectanglePresentation import differences as label_differences, observe as labels
    from convert import open_document
    from convert.adapters.solidworks.Assembly.Display.ReadAsmDisplay import ReadAsmDisplay
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Container.Format import KComponentTreeStream
    from convert.adapters.solidworks.Core.AssemblyWriting.CheckAsmShape import CheckAsmShape
    from convert.adapters.solidworks.Core.Native import ParseXml

    hashes = {key: item["sha256"] for key, item in row.items()}
    paths = {key: exact(Path(item["file"]), hashes[key]) for key, item in row.items()}
    require(paths["parent"].parent == paths["child"].parent, "strict readback requires an exact local paired child")
    raw_parent, raw_child = (paths[key].read_bytes() for key in ("parent", "child"))
    pair = {key: SldprtArchive.from_bytes(raw, paths[key].name) for key, raw in (
        ("parent", raw_parent), ("child", raw_child))}
    doc = open_document(paths["parent"], strict=True, include_brep=False, include_tessellation=False)
    doc.assert_valid()
    require(doc.source.sha256 == hashes["parent"], "strict assembly read returned a different parent")
    config = compare(doc, projected_prediction(prediction), False, hashes["child"])
    strict_refusal = refusal(lambda: CheckAsmShape(doc), ValueError,
                             "assembly root contains unprojected model content")
    selected, = doc.assembly.attributes["typed_display_states"]
    view = ReadAsmDisplay(pair["parent"], ParseXml(pair["parent"].require(KComponentTreeStream)))
    require(view is not None, "parent display XML lacks the actual configuration owner")
    from dataclasses import asdict

    joined = request_view(doc, {"configuration": view.ConfigName, "view": asdict(view)})
    require(selected["configuration_name"] == prediction["options"]["assembly_configuration"]
            and joined["name"] == display["name"] and list(map(list, joined["visibility"])) == display["visibility"],
            "the strict SDK reader lost the owned all-visible state")
    archive_audits = {key: audit(ROOT, path)["typed_stream_round_trips"] for key, path in paths.items()}
    definition = source_definition(pair["child"])
    parent = parent_store(pair["parent"], reg)
    actual_labels = labels(raw_child)
    label_delta = label_differences(source_labels, actual_labels)
    if mode == "generated":
        render = confirm_look(pair["child"], reg, appearance)
        render_delta = []
    else:
        actual, render = request_look(pair["child"], reg)
        cursor = actual.pop("StartAppearanceId")
        want = dict(appearance)
        start = want.pop("StartAppearanceId")
        render_delta = sorted(differences(json.loads(json.dumps(want)), json.loads(json.dumps(actual))))
        render = {**render, "appearance": actual, "native_renderer_field_differences": render_delta}
        if mode == "saved":
            ids = render["roles"]
            render["generated_allocator_retained"] = (
                cursor == start + 2 and ids["holder_id"] == start and ids["model_and_configuration_id"] == start + 1)
    expected_density = None if mode == "generated" else [1000.0, 0]
    physical = render if mode == "generated" else render["store"]
    density_matches = (physical["physical_density_parameter"] == expected_density
                       and physical["active_configuration_density"] == -1.0)
    for key, path in paths.items():
        exact(path, hashes[key])
    return {"strict_public_read": config, "strict_source_write_refusal": strict_refusal,
            "strict_ordinary_definition": definition["strict_guard"], "typed_display_state": selected,
            "strict_archive_audits": archive_audits, "linked_archive_streams": sum(map(len, archive_audits.values())),
            "parent_visual_replay": parent, "child_definition": definition,
            "renderer": render, "sha256": hashes, "child_labels": actual_labels, "label_discrepancies": label_delta,
            "density_owner_matches": density_matches,
            "passed": bool(density_matches and not render_delta and not label_delta
                           and render.get("generated_allocator_retained", True))}


def run(values):
    bind(ROOT)
    from ProvePlanarAssemblyIdentity import excluded_modules
    from para.concentric.ProveVisualStateStore import registry

    require(set(values) == {"files", "prediction", "appearance", "display", "source_labels"}
            and set(values["files"]) in ({"original", "generated"}, {"saved"}),
            "read back the exact disclosed frozen pair or its owned native saves")
    result = {}
    reg = registry()
    for mode, files in values["files"].items():
        try:
            result[mode] = observe(files, mode, values["prediction"], values["appearance"], values["display"],
                                   values["source_labels"], reg)
        except Exception as error:
            result[mode] = {"passed": False, "error": repr(error)}
    com = excluded_modules()
    require(not com, "the strict SDK reader imported a CAD runtime dependency")
    return {"pid": os.getpid(), "cad_runtime_imports": com, "stages": result,
            "passed": all(row["passed"] for row in result.values())}


def main():
    parser = ArgumentParser()
    parser.parse_args()
    print(json.dumps(run(json.load(sys.stdin)), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
