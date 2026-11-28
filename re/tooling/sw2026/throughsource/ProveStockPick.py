from argparse import ArgumentParser
import codecs
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
from subprocess import check_output, run
import sys


TOOL = Path(__file__).resolve()
REPO = TOOL.parents[4]
BASE = "454513a85e38f0dd03faa1c4ea52d5cff275b052"
SOURCES = {
    "original": (
        ("ThroughMultiStock03", "DisclosedNative", "ThroughMultiStock.SLDPRT"),
        "748cdbec3fe61d6801f3d606e64fe42ecba95e9a647897be3fe3790570a889f3",
        75510,
        "0b00ddbf0a6f431d13a027ea34fb4bbd73d7f509273eb4adf2fea9f89e85a9d3",
    ),
    "edited": (
        ("GeneratedTwoStockGraph01", "NativeAfterEdit.SLDPRT"),
        "236865bd1e13e246199429ad635da99a737b6280802c61df252c92d613275452",
        76337,
        "abe22b56802c3edb25229b6fab62eea78635123e4bd9f604807b2ad44032221a",
    ),
}
MODE_ERROR = "two stock lineage has an alternate profile or extrusion mode"
MAP_ERROR = "through-all presentation owner does not alias its archive map"
OWNER_ERROR = "saved cut chooser references a different producer or external owner"
ARC_KIND = "moFromSktEnt3IntSurfIdRep_c"
NEGATIVES = {
    "two-managed-atoms": "cut body atom manager contains missing or additional ownership",
    "other-component": "cut selection wrapper differs from the consumed boss atom",
    "cache-word": "face-less saved stock selector has alternate component or cache state",
    "missing-primary-chooser": "saved stock chooser has no active owner",
    "crossed-stock-chooser": "saved stock chooser is detached from its operation",
    "wrong-producer": OWNER_ERROR,
    "different-external": OWNER_ERROR,
    "wrong-arc-marker": "saved cut chooser disagrees with its actual profile markers",
    "copied-representation": MAP_ERROR,
    "different-mapped-mirror": "saved cut choosers do not mirror actual representation identities",
}
CUT_DIR = "src/convert/adapters/solidworks/Core/TypedResolved/Cuts/"
PRODUCTION = tuple(CUT_DIR + "MultiStock/" + name + ".py" for name in (
    "ReadStockPick", "ReadFaceReps", "ReadChooserPair", "ReadCutFace", "CheckPickMirror",
    "ReadStockRef", "ReadTwoStockCut", "ReadStockOps", "CheckStockMode", "CheckStockFace", "ReadStockAtoms",
)) + (
    CUT_DIR + "CheckSavedCutScope.py",
    CUT_DIR + "CheckCutWrapper.py",
    CUT_DIR + "../Presentation/CheckTreeAlias.py",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fingerprint(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def faces(operation, key):
    chooser, = operation.FieldsValue[key]["f48"]["items"]
    return tuple(row["o"] for row in chooser["o"].FieldsValue["f08"]["items"])


def representation_row(face, kind):
    return next(row for row in face.FieldsValue["f10"]
                if row["f08"] is not None and row["f08"].ClassValue.NameValue == kind)


def alter(case, link, steady, moving, cut):
    wrapper = cut.FieldsValue["f548"]["items"][0]["o"]
    root = link.ConfigValue.RootValue
    primary = faces(cut, "f4a8")
    mirror = faces(cut, "f4c0")
    first_arc = representation_row(primary[0], ARC_KIND)
    mirror_arc = representation_row(mirror[0], ARC_KIND)
    require(first_arc["f08"] is mirror_arc["f08"], "contrast started with a different native mirror")
    if case == "two-managed-atoms":
        manager = root.FieldsValue["fd88"]
        manager.update(n6c=2, atoms=manager["atoms"][1:])
    elif case == "other-component":
        wrapper.FieldsValue["f58"].FieldsValue["owner"] = replace(root)
    elif case == "cache-word":
        wrapper.FieldsValue["f104"] = 1
    elif case == "missing-primary-chooser":
        cut.FieldsValue["has_f4a8"] = 0
    elif case == "crossed-stock-chooser":
        steady.FieldsValue["f4a8"]["f68"] = cut
    elif case == "wrong-producer":
        side = representation_row(primary[0], "moFromSktEntSurfIdRep_c")["f08"]
        side.FieldsValue["f10"]["f10"].FieldsValue["f10"]["f00"] = moving.FieldsValue["f08"]
    elif case == "different-external":
        ref = first_arc["f08"].FieldsValue["f10"]["f10"]
        ref.FieldsValue["f08"] = replace(ref.FieldsValue["f08"])
    elif case == "wrong-arc-marker":
        first_arc["f08"].FieldsValue["f38"] += 1
    elif case == "copied-representation":
        first_arc["f08"] = mirror_arc["f08"] = replace(first_arc["f08"])
    elif case == "different-mapped-mirror":
        mirror_arc["f08"] = representation_row(mirror[1], ARC_KIND)["f08"]


def worker(case):
    sys.path.insert(0, str(REPO / "src"))
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.MapStockBrep import MapStockBrep
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadCacheBodies import ReadCacheBodies
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadStockCache import ReadStockCache
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadStockData import ReadStockData
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockPick import ReadStockPick
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.StockCutLineage import StockCutLineage
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import ReadPrismFrame
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
    from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from interchange.document.Behavior.DocumentIo import ToMapping

    for encoding in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be"):
        codecs.lookup(encoding)
    for dependency in (
        "interchange.brep.Validation.BrepValidate",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
        "interchange.geometry.Models.GeometryCurves",
    ):
        import_module(dependency)
    attempts = []

    def protect(event, _):
        if (event in {"open", "os.listdir", "os.scandir", "os.system", "os.exec", "os.fork", "os.posix_spawn", "os.startfile"}
                or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg."))):
            attempts.append(event)
            raise PermissionError("saved selector attempted external access: " + event)

    sys.addaudithook(protect)
    source = case if case in SOURCES else "edited"
    _, digest, size, public_digest = SOURCES[source]
    payload = sys.stdin.buffer.read(size + 1)
    require(len(payload) == size and sha256(payload).hexdigest() == digest, "worker source identity differs")
    archive = SldprtArchive.from_bytes(payload)
    link = ReadNativeLink(archive, 0)
    features = IndexFeatures(link)
    steady, moving, cut = tuple(features.values())[-5::2]
    stocks = ReadExtrude(link, steady, features), ReadExtrude(link, moving, features, NewSolid=True)
    cutter = ReadExtrude(link, cut, features, IsCut=True)
    if case in NEGATIVES:
        alter(case, link, steady, moving, cut)
        try:
            ReadStockPick(link, stocks, cutter)
        except ValueError as error:
            require(str(error) == NEGATIVES[case], str(error))
        else:
            raise ValueError("altered saved selector was admitted")
        result = {"refusal": NEGATIVES[case]}
    else:
        atoms, wrapper = ReadStockPick(link, stocks, cutter)
        key = lambda value: value.FieldsValue["f140"]
        frame_values = tuple(ReadPrismFrame(own.ProfileValue, link.ConfigValue.RootValue, features, FrontOnly=False)
                             for own in (*stocks, cutter))
        lineage = StockCutLineage(stocks, cutter, atoms, wrapper, frame_values)
        nodes, raw_brep = ReadStockData(archive, link.ConfigName + "-Partition")
        owners = ReadCacheBodies(nodes, lineage)
        grouped = MapStockBrep(nodes, raw_brep, owners)
        require(atoms.SelectedIndex == 0 and tuple(map(key, (atoms.ConsumedAtom, atoms.UntouchedAtom, atoms.ResultAtom))) == (101, 102, 103),
                "actual consumed or surviving atom identity differs")
        require(tuple(body.design_body_id for body in grouped.bodies) == ("sldprt:body:atom:102", "sldprt:body:atom:103"),
                "active partition differs from the resolved selection")
        is_original = source == "original"
        try:
            stock_cache = ReadStockCache(archive)
        except ValueError as error:
            require(not is_original and str(error) == MODE_ERROR, str(error))
        else:
            require(is_original and stock_cache.BrepValue == grouped, "full saved read changed its selected geometry")
        public = open_document(payload, source_format="solidworks.sldprt", strict=True, include_tessellation=False)
        require(fingerprint(ToMapping(public)) == public_digest, "public SDK document changed")
        face = wrapper.FieldsValue.get("ff0")
        expected_wrapper = (364, 366, 90, 103) if is_original else (344, None, 0, 0)
        result_wrapper = (wrapper.IndexValue, face.IndexValue if face is not None else None,
                          wrapper.FieldsValue["f100"], wrapper.FieldsValue["f104"])
        require(result_wrapper == expected_wrapper, "saved selector carrier differs")
        result = {
            "wrapper": result_wrapper, "consumed_atom": key(atoms.ConsumedAtom), "surviving_atoms": [body.AtomId for body in owners],
            "part_selector": wrapper.FieldsValue["f58"].IndexValue,
            "producer_ids": [row.FieldsValue["f08"] for row in (steady, moving, cut)],
            "cut_chooser_face_indexes": [[face.IndexValue for face in faces(cut, field)] for field in ("f4a8", "f4c0")],
            "physical_body_indexes": [body.KernelValue.IndexValue for body in owners],
            "public_document_sha256": public_digest, "public_design_bodies": len(public.bodies),
            "full_stock_refusal": None if is_original else MODE_ERROR,
        }
    require(not attempts, "worker attempted external access")
    return {**result, "external_access_attempts": len(attempts)}


def read_source(argument, source):
    suffix, digest, size, _ = SOURCES[source]
    locator = argument.resolve(strict=True)
    require(locator == argument.absolute() and locator.parts[-len(suffix):] == suffix
            and locator.stat().st_size == size, "use the matching disclosed source locator")
    payload = locator.read_bytes()
    require(sha256(payload).hexdigest() == digest, "disclosed file checksum differs")
    return payload


def prove(selected, edited):
    head = check_output(("git", "rev-parse", "HEAD"), cwd=REPO, text=True).strip()
    paths = {"original": selected, "edited": edited}
    samples = {case: read_source(path, case) for case, path in paths.items()}
    bound = {str((REPO / path).resolve().relative_to(REPO)): sha256((REPO / path).read_bytes()).hexdigest()
             for path in PRODUCTION}
    cases = {}
    for case in (*SOURCES, *NEGATIVES):
        process = run((sys.executable, "-I", "-B", str(TOOL), "--worker", case),
                      input=samples[case if case in SOURCES else "edited"], capture_output=True, timeout=60)
        require(process.returncode == 0, case + "\n" + process.stderr.decode("utf-8", "replace"))
        cases[case] = json.loads(process.stdout)
    require(all(samples[key] == read_source(path, key) for key, path in paths.items()), "a disclosed source changed")
    require(head == check_output(("git", "rev-parse", "HEAD"), cwd=REPO, text=True).strip()
            and all(sha256((REPO / path).read_bytes()).hexdigest() == digest for path, digest in bound.items()),
            "selector source changed during verification")
    return {
        "schema": "kit.sw2026.saved-stock-selector.v1", "base_revision": BASE, "head": head,
        "script_sha256": sha256(TOOL.read_bytes()).hexdigest(), "source_sha256": bound,
        "disclosed_sha256": {source: details[1] for source, details in SOURCES.items()},
        "guarded_processes": len(cases), "cases": cases, "native_processes": 0, "heldout_sources_read": 0,
        "generated_native_files": 0, "full_edited_sdk_admission": False, "public_writer_qualified": False,
    }


def main():
    parser = ArgumentParser(description="Validate selected stock owners in the two disclosed saved graphs")
    parser.add_argument("--selected", type=Path)
    parser.add_argument("--edited", type=Path)
    parser.add_argument("--worker", choices=(*SOURCES, *NEGATIVES))
    arguments = parser.parse_args()
    if arguments.worker:
        result = worker(arguments.worker)
    else:
        require(arguments.selected is not None and arguments.edited is not None, "both disclosed saves are required")
        result = prove(arguments.selected, arguments.edited)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
