from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from importlib import import_module
from json import dumps, loads
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
from CheckMeasuredChamfer import FORMAT, demand, pinned
from CheckScopedPlainWriter import WriterAudit

ARCHIVE = "89386f4bac8f4619bb4d37efdb1fb87cd0f52877caad193d08a323baa722178f"
SELECTORS = "a1bdd5b12a650a36b17896cb78d287a701e2df3930c85ab038716feec26311b6"
NAMES = ("EqualOriginal", "EqualEdited", "UnequalOriginal", "UnequalEdited")
BASELINE = "be5bbe87c792d76263f6b28db02ca1c5296a28ebbdf056b8b36fc76e3d94f230"
FIXTURE = ROOT / "re/solidworks/v2026/corpus/chamfer-distance-saved/EqualOriginal.SLDPRT"


def worker(raw, expected):
    demand(sha256(raw).hexdigest() == expected, "saved input changed in transport")
    sys.path.insert(0, str(ROOT / "src"))
    from convert import extract_brep, open_document
    from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
    from interchange.Features.FeatureKinds import NativeFeature

    for module in ("interchange.brep.Validation.BrepValidate", "interchange.document.Behavior.DocumentIo",
                   "interchange.document.Models.DocumentProvenance", "interchange.document.Validation.DocumentAssemblyValidate",
                   "interchange.document.Validation.DocumentFeatureValidate",
                   "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)
    for codec in ("ascii", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "latin-1", "cp1252"):
        lookup(codec)
    audit = WriterAudit(ROOT / "src", HERE.parent / "WarmUnused.SLDPRT")
    sys.addaudithook(audit.observe)
    audit.phase = "cold"
    geometry = None
    for include_brep in (False, True):
        try:
            open_document(raw, source_format=FORMAT, strict=True, include_brep=include_brep)
        except SldprtFormat as error:
            demand(str(error).startswith("SOLIDWORKS 2026 chamfer history requires the verified cold stock")
                   and str(error.__cause__) == "cold chamfer cannot own a saved body cache",
                   "strict saved inspection refused for the wrong reason")
        else:
            raise ValueError("unqualified saved chamfer history passed strict inspection")
        observed = open_document(raw, source_format=FORMAT, strict=False, include_brep=include_brep)
        warning, = [value for value in observed.diagnostics if value.code == "sldprt.chamfer_history_unresolved"]
        (chamfer,) = (step for step in observed.feature_timeline if step.kind.value == "chamfer")
        demand(warning.severity.value == "warning" and (observed.brep is not None) == include_brep
               and isinstance(chamfer.definition, NativeFeature)
               and chamfer.definition.object_data["native_class"] == "Chamfer_c",
               "permissive inspection advertised unverified editable history or lost its separate geometry lane")
        if include_brep:
            brep = observed.brep
            geometry = [len(value) for value in (brep.bodies, brep.shells, brep.faces, brep.edges, brep.vertices)]
            demand(geometry == [1, 1, 7, 15, 10] and brep.shells[0].closed,
                   "permissive inspection did not retain the closed saved chamfer B-rep")
    demand(not audit.denied and not audit.target_opens, "warm semantic boundary touched external data")
    audit.phase = "done"
    with TemporaryDirectory(prefix="KitChmfWarmRaw.") as directory:
        outputs = extract_brep(raw, directory, source_format=FORMAT)
        payloads = [sha256(value.read_bytes()).hexdigest() for value in outputs]
    demand(len(set(payloads)) == len(payloads) == 2, "raw extraction lost either physical saved payload")
    return {"source_sha256": expected, "strict_semantic_refusals": 2, "permissive_warnings": 2,
            "semantic_runtime_reads": 0, "raw_payload_sha256": payloads, "permissive_brep_topology": geometry}


def main():
    parser = ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--folder", type=Path)
    modes.add_argument("--fixture", action="store_true")
    modes.add_argument("--worker")
    args = parser.parse_args()
    if args.worker:
        print(dumps(worker(sys.stdin.buffer.read(), args.worker), sort_keys=True))
        return
    reports = ROOT / "re/solidworks/measurements/2026"
    archive, selectors = (pinned(reports / file, sha) for file, sha in (
        ("ChamferDistancePairArchive01.json", ARCHIVE), ("ChamferDistancePairSelectors01.json", SELECTORS)))
    prior = pinned(reports / "SdkMeasuredChamferRoundtrip01.json", BASELINE)["saved_inspection_controls"]
    if args.fixture:
        folder = FIXTURE.parent
        names = (FIXTURE.stem,)
    else:
        folder = args.folder.resolve(strict=True)
        demand(folder.name == "DisclosedWarmSources01", "expected only the four disclosed saved parts")
        names = NAMES
    results = {}
    for name, row, roles in zip(NAMES, archive["cases"], selectors["cases"], strict=True):
        if name not in names:
            continue
        source = folder / (name + ".SLDPRT")
        digest = row["source_sha256"]
        demand(source.is_file() and not source.is_symlink() and digest == roles["source_sha256"],
               "saved part lacks disclosed source authority")
        raw = source.read_bytes()
        demand(sha256(raw).hexdigest() == digest, "saved source differs from its measured archive")
        result = run((sys.executable, "-I", "-B", str(HERE), "--worker", digest),
                     cwd=ROOT, input=raw, capture_output=True, timeout=60, check=False)
        demand(result.returncode == 0 and not result.stderr, result.stderr.decode())
        demand(sha256(source.read_bytes()).hexdigest() == digest, "inspection changed the original source")
        observed = loads(result.stdout)
        demand(observed["raw_payload_sha256"] == prior[name]["raw_payload_sha256"],
               "the saved raw extraction payloads changed")
        results[name] = observed
    demand(set(results) == set(names), "incomplete saved inspection inventory")
    print(dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
