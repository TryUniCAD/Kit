from argparse import ArgumentParser
from hashlib import sha256
from json import dumps
from pathlib import Path
from sys import path

path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


def inspect(source, expected_hash):
    raw = source.read_bytes()
    if sha256(raw).hexdigest() != expected_hash:
        raise ValueError("the disclosed part differs from its source lock")

    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    config = link.ConfigValue
    resolved = link.ResolvedValue
    history = tuple(node.ClassValue.NameValue for node in resolved.RootsValue if node is not None)
    if history[-4:] != ("moProfileFeature_c", "moExtrusion_c", "moProfileFeature_c", "moICE_c"):
        raise ValueError("the model does not end in the disclosed blind-cut history")

    config_bytes, new_config = WriteConfigMut(config.RootValue, 19000, config.HeaderValue)
    resolved_bytes, new_resolved = WriteResolMut(
        resolved.RootsValue, resolved.ExtraFields, 19000, new_config.MapValue, resolved.ContextValue
    )
    streams = {}
    for name, data, old_graph, new_graph in (
        (link.ConfigName, config_bytes, config, new_config),
        (link.StreamName, resolved_bytes, resolved, new_resolved),
    ):
        for report in (old_graph.ReportValue, new_graph.ReportValue):
            if not report["completed"] or report["missing_schemas"] or report["provisional_schemas"]:
                raise ValueError(f"incomplete graph coverage for {name}")
        if data != archive.require(name) or old_graph.MapValue.CounterValue != new_graph.MapValue.CounterValue:
            raise ValueError(f"configuration or resolved archive changed in {name}")
        streams[name] = {
            "bytes": len(data),
            "sha256": sha256(data).hexdigest(),
            "map_counter": new_graph.MapValue.CounterValue,
            "exact_round_trip": True,
        }
    if sha256(source.read_bytes()).hexdigest() != expected_hash:
        raise ValueError("the source changed during inspection")
    return {
        "source_sha256": expected_hash,
        "history": list(history[-4:]),
        "streams": streams,
        "resolved_cut_calls": {
            name: resolved.ReportValue["schema_calls"].get(name, 0)
            for name in (
                "moICE_c", "moCompSolidBody_c", "moEndFace3IntSurfIdRep_c", "moFromSktEnt3IntSurfIdRep_c"
            )
        },
    }


def main():
    parser = ArgumentParser(description="Compare the linked archives of one hash-pinned disclosed blind-cut part")
    parser.add_argument("source", type=Path)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    print(dumps(inspect(args.source, args.sha256), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
