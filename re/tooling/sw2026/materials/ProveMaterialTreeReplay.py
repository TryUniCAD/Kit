from argparse import ArgumentParser
from codecs import lookup
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

from CorrelateMaterialTree import IO_EVENTS, ROOT, STREAM, identity, load_inputs, xml_model
from ModelMaterialTree import emit_material_tree, read_material_tree, require


def digest(raw):
    return sha256(raw).hexdigest()


def profile(model, rows):
    rows["elements"] += 1
    rows["attributes"] += len(model.attributes)
    rows["literal_appdata_lf"] += dict(model.attributes).get("appdata", "").count("\n")
    for child in model.children:
        profile(child, rows)


def measure(root):
    sys.path.insert(0, str(ROOT / "src"))
    from convert.adapters.solidworks.Container.Archive import ContainerMo
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    originals = load_inputs(root)
    source_paths = (Path(__file__), Path(__file__).with_name("ModelMaterialTree.py"))
    methods = {path.name: digest(path.read_bytes()) for path in source_paths}
    for codec in ("ascii", "latin-1", "utf-16", "utf-16-le", "utf-8"):
        lookup(codec)
    active = True
    accesses = []

    def guard(event, _):
        if active and event in IO_EVENTS:
            accesses.append(event)
            raise ValueError("material archive replay attempted a runtime file access or process launch")

    sys.addaudithook(guard)
    cases = {}
    for name, (raw, evidence) in originals.items():
        archive = SldprtArchive.from_bytes(raw)
        require(archive.format_version == 4 and ContainerMo(archive.streams) == 19000,
                "disclosed input uses unexpected native framing")
        tree = archive.require(STREAM)
        require(digest(tree) == evidence["material_tree"]["sha256"], "original material stream digest differs")
        observed, _ = xml_model(tree)
        actual = read_material_tree(tree)
        replica = emit_material_tree(actual)
        require(replica == tree and read_material_tree(replica) == actual,
                "modeled material tree did not replay the complete native bytes")
        counts = Counter()
        profile(actual, counts)
        require(counts["elements"] == len(observed), "the independent XML model has a different element inventory")
        cases[name] = {"file_sha256": digest(raw), "stream_sha256": digest(tree), "bytes": len(tree),
                       "native_id": identity(observed, evidence["owners"]), "replay_exact": True, **counts}
    active = False
    return {"schema": "kit.sw2026.disclosed-material-tree-replay.v1",
            "oracle_build": "34.5.2.0604", "stream": STREAM, "source_inputs": len(cases),
            "methods": methods, "protected_inputs_read": 0, "native_processes_started": 0, "runtime_accesses": accesses,
            "typed_xml_replay": cases, "complete_native_writer_qualified": False}


def main():
    parser = ArgumentParser()
    parser.add_argument("disclosed", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = measure(args.disclosed)
    raw = (json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with args.output.open("xb") as output:
        output.write(raw)
    print(digest(raw))


if __name__ == "__main__":
    main()
