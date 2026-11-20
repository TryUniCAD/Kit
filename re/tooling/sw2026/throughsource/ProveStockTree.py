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
FORMAT = "solidworks.sldprt"
SOURCES = {
    "original": (
        ("ThroughMultiStock03", "DisclosedNative", "ThroughMultiStock.SLDPRT"),
        "748cdbec3fe61d6801f3d606e64fe42ecba95e9a647897be3fe3790570a889f3",
        75510,
    ),
    "edited": (
        ("GeneratedTwoStockGraph01", "NativeAfterEdit.SLDPRT"),
        "236865bd1e13e246199429ad635da99a737b6280802c61df252c92d613275452",
        76337,
    ),
}
PUBLIC_ROWS = {
    "original": (8, 23, 24, 25, 22, 7, 1, 17, 18, 10, 9, 21, 16, 11, 2, 3, 4,
                 5, 6, 12, 13, 14, 15, 19, 26, 32, 33, 40, 41, 47),
    "edited": (1, 2, 3, 4, 5, 6, 13, 7, 8, 10, 11, 12, 14, 15, 16, 17, 18, 19, 21,
               22, 24, 25, 30, 31, -1, 9, 26, 27, 28, 29, 32),
}
OWNER_ROWS = {
    "original": (
        (8, 23, 24, 25, 22, 7, 1, 10, 9, 6, 21, 16, 11, 2, 3, 4, 5, 26, 32, 33, 40, 41, 47),
        ((17, 1), (18, 1), (12, 6), (13, 6), (14, 6), (15, 6)),
    ),
    "edited": (
        (1, 2, 3, 4, 5, 6, 13, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 21, 22, 24, 25),
        ((30, 13), (31, 13), (26, 9), (27, 9), (28, 9), (29, 9)),
    ),
}
ALL_OWNERS = "through-all source requires all actual persisted system owners"
STOCK_MODE = "two stock lineage has an alternate profile or extrusion mode"
NEGATIVE = {
    "populated-master": "populated sheet-metal state must remain visible",
    "named-master": "authored configuration manager state is not implicit",
    "indexed-master": "embedded sheet-metal master carries archive map identity",
    "wrong-selector": ALL_OWNERS,
    "missing-master-row": "through-all source has stripped or unaccounted public owners",
    "copied-exploded": "through-all presentation owner does not alias its archive map",
    "populated-exploded": "populated exploded-view state must remain visible",
}
PRESENTATION = "src/convert/adapters/solidworks/Core/TypedResolved/Presentation/"
OWNERS = tuple(PRESENTATION + name + ".py" for name in (
    "CheckExtras", "CheckThruRows", "CheckTreeAlias", "ConfigHelpers", "OwnedRows",
    "ProjectThruTree", "ProjectTree", "RootOrder", "ThruTreeReport",
)) + (
    "src/convert/adapters/solidworks/Archive/Bodies/Layouts/Config/ModelFields.py",
    "src/convert/adapters/solidworks/Archive/Bodies/Layouts/Config/FeatureFields.py",
    "src/convert/adapters/solidworks/Core/TypedResolved/Cuts/MultiStock/CheckStockMode.py",
    "src/convert/adapters/solidworks/Core/TypedResolved/Cuts/MultiStock/CheckStockFace.py",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fingerprint(value):
    return sha256(json.dumps(value, sort_keys=True, allow_nan=False, separators=(",", ":")).encode()).hexdigest()


def negative_model(case, model, link):
    if case not in NEGATIVE:
        return model
    root = link.ConfigValue.RootValue.FieldsValue
    master = root["f1018"]
    exploded = root["f13f8"]
    if case == "populated-master":
        master.FieldsValue.update(n370=1, f358=[exploded])
    elif case == "named-master":
        cabinet = next(row for row in link.ResolvedValue.RootsValue if row.ClassValue.NameValue == "moDetailCabinet_c")
        master.FieldsValue["f18"] = cabinet.FieldsValue["f18"]
    elif case == "indexed-master":
        master.IndexValue = exploded.IndexValue
    elif case == "wrong-selector":
        root["f1014"] = 2
    elif case == "missing-master-row":
        return replace(model, features=tuple(row for row in model.features if row.object_id != -1))
    elif case == "copied-exploded":
        root["f13f8"] = replace(exploded)
    elif case == "populated-exploded":
        exploded.FieldsValue["f368"] = {"n": 1, "items": [{"o": master}]}
    return model


def verify_tree(tree, link, source):
    evidence = tree.EvidenceValue
    require(evidence.get("status") == "ordinary_selected_two_stock_profile", str(evidence))
    require(evidence["public_timeline_preserved"] and not evidence["source_conversion_qualified"]
            and not evidence["full_native_tree_qualified"], "presentation attestation changed")
    root_ids, member_rows = OWNER_ROWS[source]
    require(evidence["root_ids"] == root_ids, "typed root order changed")
    actual_members = tuple(
        (row["native_object_id"], int(row["parent_id"].rsplit(":", 1)[1]))
        for row in evidence["rows"] if row["parent_id"] is not None
    )
    require(actual_members == member_rows and evidence["member_ids"] == tuple(row[0] for row in member_rows),
            "persisted child order or actual parent changed")
    root = link.ConfigValue.RootValue
    selector = root.FieldsValue["f1014"]
    helpers = evidence["configuration_helpers"]
    expected = (("moPrtExplViewManager_c", 19, "f13f8", 110),) if source == "original" else (
        ("moSheetMetalMaster_c", -1, "f1018", None), ("moPrtExplViewManager_c", 32, "f13f8", 123),
    )
    actual = []
    for row in helpers:
        saved = row["typed_archive_owner"]
        field = saved["owner_field"]
        node = root.FieldsValue[field]
        require(saved["stream"] == link.ConfigName and saved["owner_class"] == "moPart_c"
                and saved["owner_object_index"] == root.IndexValue
                and saved["object_index"] == node.IndexValue
                and row["stored_node_id"] == node.FieldsValue["f08"] and node.FieldsValue["f18"] is None,
                "helper lost its actual configuration owner")
        actual.append((row["class"], row["stored_node_id"], field, saved["object_index"]))
    require(tuple(actual) == expected and selector == int(source == "edited"), "wrong helper identity or presence")
    require(evidence["retained_public_ids"] == PUBLIC_ROWS[source], "typed report changed public identity order")
    return {"root_ids": root_ids, "member_parent_ids": member_rows, "helpers": actual, "f1014": selector}


def worker(case, baseline):
    sys.path.insert(0, str(REPO / "src"))
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Adapter import NativePartModel
    from convert.adapters.solidworks.Core.TypedResolved.BindFeature import BindFeature
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadStockCache import ReadStockCache
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
    from convert.adapters.solidworks.Core.TypedResolved.Presentation.ProjectTree import ProjectTree
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from interchange.document.Behavior.DocumentIo import ToMapping

    for encoding in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be"):
        codecs.lookup(encoding)
    for name in (
        "interchange.brep.Validation.BrepValidate",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
        "interchange.geometry.Models.GeometryCurves",
    ):
        import_module(name)
    attempts = []

    def protect(event, _):
        if (event in {"open", "os.listdir", "os.scandir", "os.system", "os.exec", "os.fork", "os.posix_spawn", "os.startfile"}
                or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg."))):
            attempts.append(event)
            raise PermissionError("presentation worker attempted external access: " + event)

    sys.addaudithook(protect)
    source = case if case in SOURCES else "edited"
    _, digest, size = SOURCES[source]
    payload = sys.stdin.buffer.read(size + 1)
    require(len(payload) == size and sha256(payload).hexdigest() == digest, "worker input identity differs")
    archive = SldprtArchive.from_bytes(payload)
    model = NativePartModel(archive, None)
    link = ReadNativeLink(archive, 0)
    require(tuple(item.object_id for item in model.features) == PUBLIC_ROWS[source], "native public row sequence differs")
    nodes = IndexFeatures(link)
    model = negative_model(case, model, link)
    feature_map = {
        row.object_id: BindFeature(row, nodes[row.object_id], link) if row.object_id in nodes else row
        for row in model.features
    }
    tree = ProjectTree(model, link, nodes, feature_map, TwoStocks=True)
    require(tree.FeaturesValue == tuple(feature_map[row.object_id] for row in model.features),
            "projection changed or discarded a public row")
    diagnostic = NEGATIVE.get(case, ALL_OWNERS if baseline and source == "edited" else None)
    if diagnostic is None:
        result = verify_tree(tree, link, source)
    else:
        require(tree.EvidenceValue == {"status": "unqualified", "diagnostic": diagnostic}, str(tree.EvidenceValue))
        result = {"refusal": diagnostic}
    if case in SOURCES:
        document = open_document(payload, source_format=FORMAT, strict=True, include_tessellation=False)
        body_count = len(document.bodies)
        regions = len(document.brep.regions)
        cut = document.feature_timeline[-1] if source == "original" else next(
            row for row in document.feature_timeline if row.id == "sldprt:feature:25"
        )
        require(body_count == (2 if source == "original" else 1) and regions == 2,
                "public body projection or raw regions changed")
        if source == "edited":
            try:
                ReadStockCache(archive)
            except ValueError as error:
                require(str(error) == STOCK_MODE, str(error))
            else:
                raise ValueError("edited derivative unexpectedly passed the full stock gate")
        require(bool(cut.selection_ids) == (source == "original"), "ordinary stock admission changed")
        result.update(
            retained_public_ids=PUBLIC_ROWS[source], public_document_sha256=fingerprint(ToMapping(document)),
            public_design_bodies=body_count, public_brep_regions=regions,
            full_stock_refusal=STOCK_MODE if source == "edited" else None,
        )
    require(not attempts, "worker attempted runtime file or external access")
    return {**result, "external_access_attempts": len(attempts)}


def read_source(argument, identity):
    suffix, digest, size = identity
    source = argument.resolve(strict=True)
    require(source == argument.absolute() and source.parts[-len(suffix):] == suffix
            and source.stat().st_size == size, "pass only the matching disclosed native save")
    payload = source.read_bytes()
    require(sha256(payload).hexdigest() == digest, "disclosed native save checksum differs")
    return payload


def prove(selected, edited, baseline):
    head = check_output(("git", "rev-parse", "HEAD"), cwd=REPO, text=True).strip()
    paths = {"original": selected, "edited": edited}
    payloads = {case: read_source(path, SOURCES[case]) for case, path in paths.items()}
    manifest = {owner: sha256((REPO / owner).read_bytes()).hexdigest() for owner in OWNERS}
    phases = {}
    for case in (*SOURCES,) if baseline else (*SOURCES, *NEGATIVE):
        args = (sys.executable, "-I", "-B", str(TOOL), "--worker", case)
        source = case if case in SOURCES else "edited"
        proc = run((*args, "--baseline") if baseline else args, input=payloads[source], capture_output=True, timeout=60)
        require(proc.returncode == 0, case + "\n" + proc.stderr.decode("utf-8", "replace"))
        phases[case] = json.loads(proc.stdout)
    require(all(read_source(path, SOURCES[case]) == payloads[case] for case, path in paths.items()),
            "a disclosed source changed during verification")
    require(all(sha256((REPO / owner).read_bytes()).hexdigest() == digest for owner, digest in manifest.items())
            and head == check_output(("git", "rev-parse", "HEAD"), cwd=REPO, text=True).strip(),
            "production source changed during verification")
    return {
        "schema": "kit.sw2026.two-stock-saved-presentation.v1", "base_revision": BASE, "head": head,
        "tool_sha256": sha256(TOOL.read_bytes()).hexdigest(),
        "implementation_sha256": manifest,
        "disclosed_sha256": {name: item[1] for name, item in SOURCES.items()},
        "phases": phases, "guarded_processes": len(phases), "baseline": baseline,
        "generated_native_files": 0, "heldout_sources_read": 0, "native_processes": 0,
        "public_writer_qualified": False, "full_edited_sdk_admission": False,
    }


def main():
    parser = ArgumentParser(description="Measure the two exact disclosed saved presentation graphs")
    parser.add_argument("--selected", type=Path)
    parser.add_argument("--edited", type=Path)
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--worker", choices=(*SOURCES, *NEGATIVE))
    options = parser.parse_args()
    if options.worker:
        result = worker(options.worker, options.baseline)
    else:
        require(options.selected is not None and options.edited is not None, "both disclosed saves are required")
        result = prove(options.selected, options.edited, options.baseline)
    print(json.dumps(result, sort_keys=True, allow_nan=False, indent=2))


if __name__ == "__main__":
    main()
