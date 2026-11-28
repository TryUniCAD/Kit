from argparse import ArgumentParser
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import subprocess
import sys

from ExtractTopAnnotation import canonical_json, digest, extract_top_annotation
from EncoderRoundTrip.Artifacts import read_record
from convert import open_document
from convert.adapters.solidworks.Archive.Config.ReadPartConfig import ReadPartConfig
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import (
    KConfigStream, KPartFormatId, KResolvedFeaturesStream, KeywordsStream,
)


def launch(path: Path, evidence: Path) -> subprocess.CompletedProcess:
    script = Path(__file__).with_name("ExtractTopAnnotation.py")
    return subprocess.run(
        [sys.executable, str(script), str(path), "--evidence", str(evidence)],
        capture_output=True,
    )


def build_negative(generated: bytes, scenario: str) -> bytes:
    archive = SldprtArchive.from_bytes(generated, "<generated negative control>")
    streams = dict(archive.streams)
    if scenario == "alternate_config_lane":
        streams["Contents/Config-1"] = streams[KConfigStream]
        return BuildSldprt(streams, FormatVersion=4)
    if scenario == "implicit_keyword_configuration_id":
        explicit = b'<Configuration id="0" '
        if streams[KeywordsStream].count(explicit) != 1:
            raise ValueError("negative contrast needs the generated explicit configuration row")
        streams[KeywordsStream] = streams[KeywordsStream].replace(explicit, b"<Configuration ")
        return BuildSldprt(streams, FormatVersion=4)

    graph = ReadPartConfig(archive)
    resolved = ReadResolvedMut(
        streams[KResolvedFeaturesStream], graph.VersionValue, graph.MapValue,
        {"model_compressed_stream": 1, "model_is_part": 1, "cmgr_f658": 0},
    )
    fields = graph.RootValue.FieldsValue
    owner = fields["fa48"]
    view = owner.FieldsValue["items"][0]["o"]
    match scenario:
        case "nondefault_translation":
            view.FieldsValue["f368"]["f58"] = 0.0002
        case "custom_name":
            view.FieldsValue["f358"] = "*Right"
        case "populated_reference":
            view.FieldsValue["f3d0"] = graph.RootValue
        case "borrowed_alias":
            fields["fa90"] = view
        case "multiple_views":
            other = deepcopy(view)
            other.FieldsValue["f360"] = 201
            fields["feb0"] = 201
            owner.FieldsValue.update({"n": 2, "items": [{"o": view}, {"o": other}]})
        case _:
            raise ValueError(f"unknown scenario {scenario}")
    config, written = WriteConfigMut(graph.RootValue, graph.VersionValue, graph.HeaderValue)
    streams[KConfigStream] = config
    streams[KResolvedFeaturesStream] = WriteResolMut(
        resolved.RootsValue, resolved.ExtraFields, graph.VersionValue,
        written.MapValue, resolved.ContextValue,
    )[0]
    return BuildSldprt(streams, FormatVersion=4)


def verify(args) -> dict:
    args.scratch.mkdir(parents=True, exist_ok=False)
    expected = canonical_json(read_record(args.request.read_bytes())["annotation_view"])
    report = {"positive": {}, "refusals": {}}
    for label, path in zip(
        ("vendor_original", "vendor_warmed", "generated_annotated"),
        (args.vendor_original, args.vendor_warmed, args.annotated), strict=True,
    ):
        original = path.read_bytes()
        target = args.scratch / f"{label}.json"
        result = launch(path, target)
        if result.returncode or result.stdout != expected or path.read_bytes() != original:
            raise ValueError(f"exact read-only annotation replay failed for {label}: {result.stderr!r}")
        row = read_record(target.read_bytes())
        if row["source_sha256"] != digest(original) or row["annotation_sha256"] != digest(result.stdout):
            raise ValueError(f"annotation evidence lost its custody for {label}")
        report["positive"][label] = row

    def refuse_process(label: str, path: Path, expected_message: str) -> None:
        target = args.scratch / f"{label}Evidence.json"
        before = path.read_bytes()
        result = launch(path, target)
        detail = result.stderr.decode().strip()
        if (result.returncode != 1 or result.stdout or target.exists()
                or detail != expected_message or path.read_bytes() != before):
            raise ValueError(f"{label} failed its read-only process refusal: {detail}")
        report["refusals"][label] = {"sha256": digest(before), "stage": "source process", "detail": detail}

    count = "Top annotation requires one direct saved view"
    identity = "Top annotation requires the sole default Top view and its display high-water ID"
    fields = "Top annotation uses an unsupported pose, reference or subtype field"
    refuse_process("generated_plain_absent", args.plain, count)
    generated = args.annotated.read_bytes()
    for scenario, detail in (
        ("nondefault_translation", fields),
        ("custom_name", identity),
        ("populated_reference", fields),
        ("borrowed_alias", "Top annotation owner and view must have exclusive typed references"),
        ("multiple_views", count),
        ("alternate_config_lane", "Top annotation requires only the physical Config-0 lane without a Kit carrier"),
        ("implicit_keyword_configuration_id", "Top annotation requires matching explicit active configuration identity"),
    ):
        variant = args.scratch / f"{scenario}.SLDPRT"
        variant.write_bytes(build_negative(generated, scenario))
        refuse_process(scenario, variant, detail)

    companion = open_document(generated, source_format=KPartFormatId, strict=True)
    wrong_source = replace(companion, source=replace(companion.source, sha256="0" * 64))
    configuration, = companion.configurations
    wrong_configuration = replace(companion, configurations=(replace(configuration, id="configuration:changed"),))
    for label, wrong in (("source_sha_mismatch", wrong_source), ("neutral_configuration_id_mismatch", wrong_configuration)):
        try:
            extract_top_annotation(generated, wrong)
        except ValueError as error:
            report["refusals"][label] = {"stage": "source API", "detail": str(error)}
        else:
            raise ValueError(f"{label} was accepted by the source API")
    return report


if __name__ == "__main__":
    parser = ArgumentParser(description="Verify the source-only Top annotation extraction boundary")
    parser.add_argument("--vendor-original", required=True, type=Path)
    parser.add_argument("--vendor-warmed", required=True, type=Path)
    parser.add_argument("--annotated", required=True, type=Path)
    parser.add_argument("--plain", required=True, type=Path)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--scratch", required=True, type=Path)
    sys.stdout.buffer.write(canonical_json(verify(parser.parse_args())))
