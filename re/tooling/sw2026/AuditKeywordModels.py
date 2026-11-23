from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
from subprocess import check_output, run
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent)]

from AuditKeywordCorpus import pinned_documents, require
from AuditNestedNeutralComposition import CASES, checked as checked_nested
from AuditRecoveredLadder import MANIFEST, checked as checked_recovered
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import KeywordFeature
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordRef import KeywordRef
from convert.adapters.solidworks.Archive.Construction.Metadata.ReadKeyIndex import ReadKeyIndex
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from tests.Convert.Solidworks.Research.Construction.Assembly.MakeAsmCase import MakeAsmCase


SOURCE = "9dca0bd65a4762962b0d71b896cdd354eb405a98"
SOURCE_TREE = "2074538fc5f621e27e12283583d1b088edc9911d"
KEYWORDS = "swXmlContents/KeyWords"
METADATA = Path("src/convert/adapters/solidworks/Archive/Construction/Metadata")
CONSTRUCTION = METADATA.parent
PROJECTORS = (
    "Assembly/Xml/MakeAsmKeyIndex.py",
    "Assembly/Xml/MakeAsmKeys.py",
    "NestedAssemblies/MakeNestedKeys.py",
)


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def digest(data):
    return sha256(data).hexdigest()


def recovered_documents():
    manifest = json.loads(checked_recovered("Manifest.json", MANIFEST))
    for case in manifest["cases"]:
        require(case["capture_status"] == "complete_controlled_batch", "recovered source lacks its native bracket")
        for member in case["files"]:
            path = member["native_path"]
            yield path, checked_recovered(path, member["source_sha256"])


def check_source_owners(archive, index, assembly):
    features = index.FeatureValues
    refs = tuple(value for value in features if type(value) is KeywordRef)
    sheet_metal = tuple(value for value in features if value.IdValue == -1)
    if not assembly and not sheet_metal:
        require(not refs, "part has an unbound assembly occurrence")
        return {}
    link = ReadNativeLink(archive, 0)
    model = link.ConfigValue.RootValue
    if sheet_metal:
        master = model.FieldsValue["f1018"]
        require(len(sheet_metal) == 1 and master.ClassValue.NameValue == "moSheetMetalMaster_c"
                and master.FieldsValue["f08"] == -1 and master.FieldsValue["f18"] is None
                and master.FieldsValue["n370"] == 0 and master.FieldsValue["f358"] == [],
                "sheet metal marker lacks its actual empty configuration owner")
    if not assembly:
        return {"empty_sheet_metal_owners": 1}
    occurrences = tuple(row["o"] for row in model.FieldsValue.get("f68", {}).get("list", {}).get("items", ()))
    actual = tuple(sorted((node.FieldsValue["f08"], ReadNodeName(node),
                           PureWindowsPath(ReadFileKey(node.FieldsValue["f3b0"])[0]).stem) for node in occurrences))
    require(actual == tuple(sorted((row.IdValue, row.NameValue, row.FileStem) for row in refs)),
            "occurrence index does not join its binary reference and named file token")
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000).RootValue
    config = manager.FieldsValue["f360"]
    require([(value.IdValue, value.NameValue) for value in index.ConfigValues]
            == [(config.FieldsValue["f08"], ReadNodeName(config))], "active configuration index owner differs")
    header = link.ConfigValue.HeaderValue
    require(header.FieldsValue["f38"].FieldsValue["shared"]["f28"] == index.Timestamp,
            "assembly index event does not join its actual self-file epoch")
    environment = model.FieldsValue["f1e0"]
    require(sum(node is environment for node in link.ResolvedValue.RootsValue) == 1,
            "assembly environment has an unbound resolved root")
    return {"assembly_config_and_event_owners": 1, "occurrence_owners": len(refs),
            "saved_environment_requires_distinct_owner_mapping": environment.FieldsValue.get("owner") is not model}


def cohort(documents, expected):
    counts = Counter()
    manifest = sha256()
    for path, raw in documents:
        archive = SldprtArchive.from_bytes(raw)
        require(archive.format_version == 4 and ContainerMo(archive.streams) == 19000,
                "keyword corpus archive format differs")
        stream = archive.require(KEYWORDS)
        index = ReadKeyIndex(stream)
        require(index.ToBytes() == stream, "typed keyword model changed source bytes")
        references = tuple(row for row in index.FeatureValues if type(row) is KeywordRef)
        features = tuple(row for row in index.FeatureValues if type(row) is KeywordFeature)
        dimensions = tuple(dim for row in features for dim in row.DimensionValues)
        counts.update({"streams_exact": 1, "compact": int(index.CompactTags), "spaced": int(not index.CompactTags),
                       "features": len(features), "configurations": len(index.ConfigValues),
                       "references": len(references), "dimensions": len(dimensions),
                       "radius": sum(dim.PrefixValue == "radius" for dim in dimensions),
                       "diameter": sum(dim.PrefixValue == "diameter" for dim in dimensions),
                       "degree": sum(dim.UnitValue == "degree" for dim in dimensions),
                       "native_cut_order": sum(bool(row.ChildIds) and row.RootValue is not None
                                               and index.NativeRows for row in features),
                       "empty_dissectable_sketches": sum(row.TagValue == "Sketch" and row.KindValue is None
                                                         and not row.DimensionValues for row in features)})
        counts.update(check_source_owners(archive, index, Path(path).suffix.casefold() == ".sldasm"))
        manifest.update(json_bytes((path, digest(raw), digest(stream))))
    require(counts["streams_exact"] == expected, "keyword cohort cardinality differs")
    return {"counts": dict(counts), "input_and_stream_manifest_sha256": manifest.hexdigest()}


def worker(root, name, arguments, request):
    result = run((sys.executable, "-I", "-B", str(root / name), *arguments), cwd=root,
                 input=json_bytes(request), capture_output=True, check=False, timeout=120)
    require(result.returncode == 0 and not result.stderr, result.stderr.decode(errors="replace")[-3500:])
    data = json.loads(result.stdout)
    require(data["passed"], "assembly worker did not pass its construction boundary")
    return data


def compare_generated(baseline, workspace):
    actual = check_output(("git", "rev-parse", "HEAD:src"), cwd=baseline, text=True).strip()
    changed = check_output(("git", "status", "--porcelain=v1", "--", "src"), cwd=baseline)
    require(actual == SOURCE_TREE and not changed, "baseline does not contain the pinned former writer")
    normal = {}
    for kind in ("coincident", "parallel", "distance"):
        for axis in "xyz":
            for variant in (False, True):
                request = MakeAsmCase(kind, axis, variant)
                got = []
                for root in (baseline, ROOT):
                    data = worker(root, "re/tooling/sw2026/SdkAssemblyProcess.py", (str(root),), request)
                    require(not data["runtime_input_file_reads"], "ordinary assembly writer read a runtime input")
                    got.append({key: {name: value for name, value in data[key].items() if name != "blob"}
                                for key in ("assembly", "child")})
                require(got[0] == got[1], "whole ordinary assembly/child pair differs")
                normal[f"{kind}/{axis}/{int(variant)}"] = {name: row["sha256"] for name, row in got[1].items()}
    nested = {}
    for case, pin in CASES.items():
        fixture = json.loads(checked_nested(workspace / case / "Fixture.json", pin))
        raw = checked_nested(workspace / case / "NeutralRequest.json", fixture["request_sha256"])
        request = {"request": json.loads(raw)}
        got = []
        for root in (baseline, ROOT):
            data = worker(root, "re/tooling/sw2026/AuditNestedNeutralComposition.py", ("--worker",), request)
            require(not data["runtime_file_reads"], "nested assembly writer read a runtime input")
            got.append(data["outputs"])
        require(got[0] == got[1], "whole nested assembly output differs")
        nested[case] = {name: row["sha256"] for name, row in got[1].items()}
    return {"ordinary": normal, "nested": nested, "fresh_processes": 2 * (len(normal) + len(nested)),
            "runtime_writer_input_reads": 0}


def codec_fingerprint():
    names = {file.relative_to(ROOT) for file in (ROOT / METADATA).glob("*.py")}
    names.update(CONSTRUCTION / path for path in PROJECTORS)
    return digest(json_bytes({str(path): digest((ROOT / path).read_bytes()) for path in sorted(names)}))


def main():
    parser = ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("disclosures", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    codec = codec_fingerprint()
    result = {
        "schema": "kit.sw2026.typed-keyword-index.v1",
        "input_git_revision": SOURCE,
        "input_recovered_manifest_sha256": MANIFEST,
        "production_baseline_tree": SOURCE_TREE,
        "tracked": cohort(pinned_documents(SOURCE), 100),
        "recovered": cohort(recovered_documents(), 111),
        "generated_regression": compare_generated(args.baseline.resolve(), args.disclosures.resolve()),
        "native_processes_started": 0, "heldout_inputs_read": 0,
        "codec_sources_sha256": codec,
        "script_sha256": digest(HERE.read_bytes()),
    }
    require(codec_fingerprint() == codec, "keyword codec changed during the audit")
    raw = json_bytes(result)
    with args.output.open("xb") as output:
        output.write(raw)
    print(json.dumps({"sha256": digest(raw), "typed_streams_exact": 211,
                      "ordinary": 18, "nested": 2, "generated_worker_processes": 40}))


if __name__ == "__main__":
    main()
