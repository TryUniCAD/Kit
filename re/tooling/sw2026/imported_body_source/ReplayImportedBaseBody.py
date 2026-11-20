from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName


SOURCE = "13f1ef12ab727323a826ead989087079f44e9b24a4326aa9b65be61c9d81f325"
CLASS = "moBaseBody_c"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def measure(path, expected_sha256=SOURCE):
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == expected_sha256, "use the exact disclosed imported source witness")
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    config, seed = WriteConfigMut(link.ConfigValue.RootValue, 19000, link.ConfigValue.HeaderValue)
    resolved, graph = WriteResolMut(
        link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields, 19000,
        seed.MapValue, link.ResolvedValue.ContextValue,
    )
    manager = archive.require("Contents/CMgr")
    matched = {
        "Contents/Config-0": config, "Contents/Config-0-ResolvedFeatures": resolved,
        "Contents/CMgr": WriteCmgrMut(ReadCmgrMut(manager, 19000).RootValue, 19000),
    }
    for name in ("Header2", "Contents/Config-0-ModelHeader"):
        matched[name] = WriteHeadGraph(ReadHeaderGraph(archive.require(name), 19000), 19000)
    require(all(archive.require(name) == data for name, data in matched.items()),
            "a linked witness stream changed on typed re-emission")
    imported, = (node for node in graph.RootsValue if node.ClassValue.NameValue == CLASS)
    fields = imported.FieldsValue
    atom, = (row["o"] for row in fields["f528"]["items"])
    text = [fields["source_filename"], fields["local_storage_key"]]
    words = [fields["local_body_switch"], fields["segment_mesh_count"]]
    return {
        "schema": "kit.sw2026.imported-base-body-witness-replay.v1",
        "source_sha256": expected_sha256, "feature_id": fields["f08"], "feature_name": ReadNativeName(imported),
        "model_version": link.ConfigValue.VersionValue, "config_map": seed.MapValue.CounterValue,
        "resolved_map": graph.MapValue.CounterValue, "resolved_base": graph.MapBase,
        "class": CLASS, "runtime_schema": imported.ClassValue.SchemaValue,
        "observed_suffix_text": text, "observed_suffix_words": words,
        "atom_body_name": None if atom.FieldsValue["f18"] is None else ReadNativeName(atom),
        "matched_streams": {name: {"bytes": len(data), "sha256": sha256(data).hexdigest()} for name, data in matched.items()},
        "heldout_payloads_read": 0, "native_writer_outputs": 0,
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Replay the measured imported base-body archive witness")
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    print(json.dumps(measure(args.source), indent=2, sort_keys=True))
