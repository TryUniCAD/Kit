from base64 import b64encode
from codecs import lookup
from hashlib import sha256
import json
import os
from pathlib import Path
import sys


ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from SdkAssemblySettings import assembly_settings, occurrence_settings
from SdkBlindPartSettings import settings
from SdkNativeRoundTrips import roundtrips
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.CheckTarget import CheckTarget
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.MakePartTarget import MakePartTarget
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.MakeNestedAsm import MakeNestedAsm
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.TargetPlacement import TargetPlacement
from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindPart
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Container.Container import SldprtArchive
from interchange.serialization.Deserialize import FromData
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors


CODECS = tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    require(set(REQUEST) == {"root", "definitions"}, "nested generation requires its complete declared neutral definition DAG")
    definitions = {}
    for row in REQUEST["definitions"]:
        require(row["kind"] in ("part", "assembly") and isinstance(row["id"], str) and row["id"] and row["id"] not in definitions,
                "nested definitions require unique identities and supported native kinds")
        require(set(row) == ({"id", "kind", "request"} if row["kind"] == "part" else {"id", "kind", "request", "occurrences"}),
                "nested definition includes an unsupported or missing field")
        definitions[row["id"]] = row
    require(REQUEST["root"] in definitions and definitions[REQUEST["root"]]["kind"] == "assembly", "nested root must identify its declared assembly")
    documents = {}
    active = set()

    def construct(identity):
        require(identity in definitions, "an occurrence targets an undeclared definition")
        if identity in documents:
            return documents[identity]
        require(identity not in active, "neutral definition graph contains a cycle")
        active.add(identity)
        row = definitions[identity]
        if row["kind"] == "part":
            values = row["request"]
            require(set(values) == {"document", "settings"}, "part definition requires its actual neutral document and explicit settings")
            target = MakePartTarget(MakeBlindPart(FromData(values["document"]), settings(values["settings"])))
        else:
            placements = []
            for occurrence in row["occurrences"]:
                require(set(occurrence) == {"target", "occurrence"} and set(occurrence["occurrence"]) == {"name", "origin", "u", "v"},
                        "ordinary nested placement includes unsupported state or missing geometry")
                item, = occurrence_settings((occurrence["occurrence"],))
                placements.append(TargetPlacement(construct(occurrence["target"]), item))
            target = MakeNestedAsm(assembly_settings(row["request"]), tuple(placements))
        CheckTarget(target)
        active.remove(identity)
        documents[identity] = target
        return target

    root = construct(REQUEST["root"])
    require(set(documents) == set(definitions), "nested input has unreachable definitions")
    require(sum(value.RootValue.ClassValue.NameValue == "moAssembly_c" for value in documents.values()) >= 2,
            "a genuine nested bundle requires an assembly target and its containing assembly")
    records = {}
    total = 0
    for identity, target in documents.items():
        kind = target.RootValue.ClassValue.NameValue
        archive = SldprtArchive.from_bytes(target.BytesValue, identity)
        link, mates, manager_header, manager, proof = roundtrips(archive, kind == "moAssembly_c")
        total += len(proof)
        require(link.ConfigValue.RootValue.ClassValue.NameValue == kind and (mates is None or not mates.RootsValue),
                "the complete SDK nested profile changed model kind or added mates")
        records[identity] = {"kind": definitions[identity]["kind"], "path": ReadFileKey(target.HeaderValue.FieldsValue["f38"])[1],
                             "bytes": len(target.BytesValue), "sha256": sha256(target.BytesValue).hexdigest(), "blob": b64encode(target.BytesValue).decode("ascii"),
                             "activity": target.ActivityValue, "direct_references": len(target.ReferenceValues),
                             "target_ids": [next(key for key, value in documents.items() if value.RootValue is child.RootValue) for child in target.ChildTargets],
                             "configuration_map_counter": target.ConfigValue.MapValue.CounterValue, "resolved_map_counter": target.ResolvedValue.MapValue.CounterValue,
                             "streams": proof}
    imports = sorted(name for name, module in tuple(sys.modules.items()) if str(getattr(module, "__file__", "")).startswith(str(ROOT / "re") + "/")
                     and name not in ("__main__", "SdkAssemblySettings", "SdkBlindPartSettings", "SdkNativeRoundTrips"))
    require(not imports and not AUDIT.DeniedReads, "SDK nested generation imported research rules or read runtime inputs")
    return {"passed": True, "worker_pid": os.getpid(), "root": REQUEST["root"], "documents": records,
            "definition_count": len(documents), "expanded_root_occurrences": root.ActivityValue, "typed_stream_round_trips": total,
            "runtime_input_file_reads": len(AUDIT.DeniedReads), "sdk_runtime_research_imports": len(imports),
            "native_acceptance": False, "public_writer_qualified": False, "heldout_inputs_read": 0}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
