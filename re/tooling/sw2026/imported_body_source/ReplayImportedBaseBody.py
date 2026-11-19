from argparse import ArgumentParser
from contextlib import contextmanager
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
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
VIRTUALS = {
    (CLASS, 0x4B8): "moConcept_c.SerializeLWData",
    (CLASS, 0x4C0): "moConcept_c.SerializeResolvedData",
    (CLASS, 0x3F8): True,
    (CLASS, 0x3E8): "moFeature_c.SerializeXmlData",
}
WITNESS_LAYOUT = (
    NativeField("Base", "moBodyFeature_c"),
    NativeField("Text", "import_suffix_first_text"),
    NativeField("Scalar", "import_suffix_first_word", "i32"),
    NativeField("Text", "import_suffix_second_text"),
    NativeField("Scalar", "import_suffix_second_word", "i32"),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


@contextmanager
def witness_grammar(module_name):
    module = import_module("convert.adapters.solidworks.Archive.Resolved." + module_name)
    ordinary = module.MakeResolvedCtx

    def source_context(*args, **kwargs):
        context = ordinary(*args, **kwargs)
        require(context.VersionValue == 19000 and context.FlagsValue == {
            "model_compressed_stream": 1, "model_is_part": 1, "cmgr_f658": 1,
        }, "imported body witness requires its measured archive context")
        context.VirtualValue = {**context.VirtualValue, **VIRTUALS}
        context.LayoutsValue = {**context.LayoutsValue, CLASS: WITNESS_LAYOUT}
        context.SchemasValue = {**context.SchemasValue, CLASS: (1,)}
        return context

    module.MakeResolvedCtx = source_context
    try:
        yield
    finally:
        module.MakeResolvedCtx = ordinary


def measure(path, expected_sha256=SOURCE):
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == expected_sha256, "use the exact disclosed imported source witness")
    archive = SldprtArchive.from_bytes(raw)
    with witness_grammar("ReadResolvedMut"):
        link = ReadNativeLink(archive, 0)
    config, seed = WriteConfigMut(link.ConfigValue.RootValue, 19000, link.ConfigValue.HeaderValue)
    with witness_grammar("WriteResolMut"):
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
    text = [fields[f"import_suffix_{index}_text"] for index in ("first", "second")]
    words = [fields[f"import_suffix_{index}_word"] for index in ("first", "second")]
    return {
        "schema": "kit.sw2026.imported-base-body-witness-replay.v1",
        "source_sha256": expected_sha256, "feature_id": fields["f08"], "feature_name": ReadNativeName(imported),
        "model_version": link.ConfigValue.VersionValue, "config_map": seed.MapValue.CounterValue,
        "resolved_map": graph.MapValue.CounterValue, "resolved_base": graph.MapBase,
        "class": CLASS, "runtime_schema": imported.ClassValue.SchemaValue,
        "observed_suffix_text": text, "observed_suffix_words": words,
        "atom_body_name": None if atom.FieldsValue["f18"] is None else ReadNativeName(atom),
        "matched_streams": {name: {"bytes": len(data), "sha256": sha256(data).hexdigest()} for name, data in matched.items()},
        "suffix_producer_fields_classified": False, "heldout_payloads_read": 0, "native_writer_outputs": 0,
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Replay the measured imported base-body archive witness")
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    print(json.dumps(measure(args.source), indent=2, sort_keys=True))
