import argparse
import codecs
from hashlib import sha256
from importlib import import_module
import json
from ntpath import basename, splitext
from pathlib import Path
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sdk", type=Path, required=True)
    args = parser.parse_args()
    row = json.loads(sys.stdin.read())
    sys.path[:0] = [str(args.sdk / "src"), str(Path(__file__).resolve().parent)]
    from convert import open_document
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
    from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHeader import ReadMgrHeader
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
    from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
    from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ProjectRevolve import ProjectRevolve
    from dataclasses import replace
    from BuildChronology02 import compose
    from MakeRevolveRequest01 import make_request
    for encoding in ("ascii", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "latin-1"):
        codecs.lookup(encoding)
    for name in ("interchange.document.Behavior.DocumentIo", "interchange.brep.Validation.BrepValidate", "interchange.document.Models.DocumentProvenance", "interchange.document.Validation.AngleRevValidate", "interchange.document.Validation.DocumentAssemblyValidate", "interchange.document.Validation.DocumentFeatureValidate", "interchange.document.Validation.DocumentReferenceValidate", "interchange.document.Validation.PlaneRevValidate", "interchange.document.Validation.DistExtValidate"):
        import_module(name)
    state = {"enabled": False, "attempts": []}

    def audit(event, arguments):
        if state["enabled"] and (event == "open" or event.startswith(("subprocess.", "socket.")) or event in ("os.system", "os.fork", "os.posix_spawn", "ctypes.dlopen")):
            state["attempts"].append(event)
            raise RuntimeError("part identity construction attempted external runtime access")

    sys.addaudithook(audit)
    result = {"schema": "kit.sw2026.part-chronology-identity-process.v1", "passed": False, "heldout_inputs_read": 0, "native_processes": 0}
    state["enabled"] = True
    try:
        original, base_settings = make_request(row["base_spec"])
        baseline = compose(original, base_settings, "coupled")
        require(sha256(baseline["bytes"]).hexdigest() == row["base_sha256"], "independent identity prerequisite changed a frozen candidate")
        document, settings = make_request(row["base_spec"])
        output = SelfFileInput(row["output_path"], settings.HeaderValue.CreatedAt + 71)
        try:
            CheckPartInput(document, replace(settings, OutputValue=output), ProjectRevolve(document))
        except ValueError as error:
            require(str(error) == "native self filename must match the actual modeled part name", "ordinary preparation refusal changed")
            preparation_refusal = str(error)
        else:
            raise AssertionError("ordinary preparation unexpectedly expanded its filename policy")
        candidate, replay = compose(document, settings, "split", output), compose(document, settings, "split", output)
        require(candidate["bytes"] == replay["bytes"], "explicit target identity is not deterministic")
        model_name = document.metadata["name"]
        output_stem = splitext(basename(row["output_path"]))[0]
        require(model_name != output_stem, "independent identity case must distinguish actual model name from destination stem")
        archive = SldprtArchive.from_bytes(candidate["bytes"])
        identities = []
        for name in ("Header2", "Contents/Config-0-ModelHeader"):
            graph = ReadHeaderGraph(archive.require(name), 19000)
            require(WriteHeadGraph(graph, 19000) == archive.require(name), "explicit target header failed wire identity")
            fields = graph.FieldsValue
            self_fields = fields["f38"].FieldsValue
            shared = self_fields["shared"]
            require(shared["h10"].FieldsValue["value"].TextValue == model_name and shared["h18"].FieldsValue["value"].TextValue == row["output_path"], "target path replaced or conflated the actual model name")
            require(shared["f28"] == fields["f70"] == candidate["clocks"].CreatedAt and self_fields["f60"] == candidate["input"].OutputValue.SavedAt, "file identity borrowed an unrelated event clock")
            identities.append({"stream": name, "actual_model_name": model_name, "output_stem": output_stem, "path_utf8_sha256": sha256(row["output_path"].encode()).hexdigest(), "self_creation": shared["f28"], "self_save": self_fields["f60"]})
        manager_save = ReadMgrHeader(archive.require("Contents/CMgrHdr2"), 19000).RootValue.FieldsValue["f60"]
        require(manager_save == candidate["input"].OutputValue.SavedAt, "existing admitted manager save policy changed")
        loaded = open_document(candidate["bytes"], source_format="solidworks.sldprt", strict=True)
        before = open_document(baseline["bytes"], source_format="solidworks.sldprt", strict=True)
        loaded.assert_valid()
        typed_model = ReadNativeLink(archive, 0).ConfigValue.RootValue
        require(typed_model.FieldsValue["f18"].FieldsValue["f08"] == model_name, "actual typed model identity changed")
        require("name" not in loaded.metadata, "flat public model name projection changed and requires a fresh contract check")
        require(loaded.feature_timeline == before.feature_timeline and loaded.sketches == before.sketches and loaded.parameters == before.parameters and loaded.bodies == before.bodies and loaded.brep == before.brep, "ordinary strict read changed authored geometry")
        require(loaded.brep is not None and not loaded.brep_payloads and not loaded.brep.validate(frozenset(value.id for value in loaded.bodies)), "explicit identity did not preserve validated cacheless geometry")
        result.update(passed=True, sha256=sha256(candidate["bytes"]).hexdigest(), deterministic_two_builds=True, identities=identities, manager_save_epoch=manager_save, typed_model_name_retained=True, flat_public_model_name_projected=False, geometry_unchanged=True, full_original_source_preparation_admitted=False, ordinary_preparation_refused=True, ordinary_preparation_diagnostic=preparation_refusal, lower_self_owner_experiment_only=True)
    finally:
        state["enabled"] = False
    result["runtime_external_attempts"] = state["attempts"]
    result["sdk_modules"] = sorted({module.__file__ for name, module in sys.modules.items() if (name == "convert" or name.startswith(("convert.", "interchange."))) and getattr(module, "__file__", None)})
    print(json.dumps(result, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
