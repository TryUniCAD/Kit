from argparse import ArgumentParser
from codecs import lookup
from contextlib import contextmanager
from dataclasses import asdict, replace
from pathlib import Path
from subprocess import run
from xml.sax.saxutils import quoteattr
import json
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from CorrelateMaterialTree import (
    DIAGNOSTIC, DISCLOSED, HERE as CORRELATION, IO_EVENTS, OWNERS, ROOT, STREAM,
    URI, checked, digest, encode, load_inputs, require,
)


BASE = "f818c0c665c8c1d538cad7e1a6bcfade14ee36d0"
CORRELATION_RECEIPT = "be4df2e8449c6d0bbd883ae439b658e16ca3d915a6a57564096b2096952d2106"
LEDGER = "re/solidworks/measurements/2026"
SDK = "src/convert/adapters/solidworks"
ASSIGNED_CASES = {
    f"D0{index}{name}/{stage}"
    for index, name in ((1, "Corner"), (2, "Center"))
    for stage in ("Author", "Swap", "Depth")
} | {"Diagnostic"}


def refusal(action, expected):
    try:
        action()
    except ValueError as error:
        require(expected in str(error), "unexpected refusal: " + str(error))
        return str(error)
    raise ValueError("accepted invalid assignment: " + expected)


@contextmanager
def altered(fields, key, value):
    previous = fields[key]
    fields[key] = value
    try:
        yield
    finally:
        fields[key] = previous


def author_tree(row, *, configuration=None, identity=None, density=None, duplicate=False, doctype=False):
    prefix = f"{row.CatalogValue}|{row.MaterialName}"
    config = quoteattr(configuration if configuration is not None else row.CfgName)
    native_id = row.NativeId if identity is None else identity
    rho = row.DensityValue if density is None else density
    config_row = f"<configuration name={config} material={quoteattr(f'{prefix}|{row.NativeId}')}/>"
    return (
        ("<!DOCTYPE materials>" if doctype else "")
        + f'<m:materials xmlns:m="{URI}"><curves/><classification><material name={quoteattr(prefix)} '
        + f'matid="{native_id}"><physicalproperties><DENS value="{rho}"/></physicalproperties>'
        + f"</material></classification><configurationslist>{config_row * (2 if duplicate else 1)}"
        + "</configurationslist></m:materials>"
    ).encode("utf-16")


def archive_contrasts(archive, row, read):
    def tree_archive(value):
        return replace(archive, records=tuple(
            record if record.name != STREAM else replace(record, data=value) for record in archive.records
        ))

    require(read(tree_archive(author_tree(row))) == row, "independently framed matching identity was refused")
    alternatives = {
        "wrong_xml_config": {"configuration": row.CfgName + " other"},
        "wrong_xml_material_id": {"identity": row.NativeId + 1},
        "wrong_xml_density": {"density": row.DensityValue + 1.0},
        "duplicate_xml_config": {"duplicate": True},
        "xml_doctype": {"doctype": True},
    }
    declined = {
        role: refusal(lambda: read(tree_archive(author_tree(row, **case))), "MATERIALTREE does not corroborate")
        for role, case in alternatives.items()
    }
    declined["missing_xml"] = refusal(
        lambda: read(replace(archive, records=tuple(r for r in archive.records if r.name != STREAM))),
        "required stream is missing",
    )
    declined["wrong_container_version"] = refusal(
        lambda: read(replace(archive, format_version=3)), "requires an ordinary version-19000 part Config-0",
    )
    declined["xml_framing"] = refusal(
        lambda: read(tree_archive(author_tree(row).decode("utf-16").encode())), "UTF-16LE framing",
    )
    return declined


def graph_checks(part, cmgr, header, bind, contrasts):
    def metadata(node):
        return [node.ClassValue.NameValue, node.IndexValue, node.StartOffset, node.EndOffset]

    model = part.RootValue.FieldsValue
    manager = cmgr.RootValue.FieldsValue
    config_node = manager["f368"]
    config = config_node.FieldsValue
    header_node = header.RootValue.FieldsValue["f08"]["items"][0]["o"]
    density = model["f1420"].FieldsValue["f08"]
    atom = model["fd88"]["atoms"][0]["o"]
    require(bind(part, cmgr, header).DensityValue == density.FieldsValue["f58"],
            "archive binding differs from the actual part parameter")
    contrast = (
        ("detached_active_pointer", manager, "f368", replace(config_node), "does not own the selected Config-0"),
        ("detached_density_node", model["f1420"].FieldsValue, "f08", replace(density), "detached from its archive map"),
        ("shifted_density_span", density, "StartOffset", 0, "density is absent, overridden or inconsistent"),
        ("stale_active_header", header_node.FieldsValue, "f38", config["f860"] + 1, "does not own the selected Config-0"),
        ("separate_density_override", density.FieldsValue, "f68", 1, "density is absent, overridden or inconsistent"),
        ("split_density", config, "fc50", density.FieldsValue["f58"] + 1.0, "density is absent, overridden or inconsistent"),
        ("detached_atom", model["fd88"]["atoms"][0], "o", replace(atom), "detached from its archive map"),
        ("body_assignment_table", config, "n430", 1, "unqualified body or custom material override"),
        ("custom_density_table", manager, "n600", 1, "unqualified body or custom material override"),
        ("separate_body_scene", model["f938"], "n58", 1, "unqualified body or custom material override"),
        ("conflicting_visual_identity", model["f78"].FieldsValue["f20"], "f20", "Steel", "visual owners disagree"),
        ("unqualified_texture_selector", config["f78"].FieldsValue["f20"], "has98", 1, "visual owners disagree"),
    )
    refused = {}
    for role, fields, key, value, message in contrast if contrasts else ():
        if fields is density:
            saved = density.StartOffset
            density.StartOffset = value
            try:
                refused[role] = refusal(lambda: bind(part, cmgr, header), message)
            finally:
                density.StartOffset = saved
        else:
            with altered(fields, key, value):
                refused[role] = refusal(lambda: bind(part, cmgr, header), message)
    if contrasts:
        part_material = model["f78"].FieldsValue["f20"]
        config_material = config["f78"].FieldsValue["f20"]
        ident = config_material["f20"]
        if not isinstance(ident, str):
            ident = ident.TextValue
        with altered(part_material, "f20", ident.rsplit("|", 1)[0]), altered(config_material, "f20", ident.rsplit("|", 1)[0]):
            refused["missing_native_id"] = refusal(
                lambda: bind(part, cmgr, header), "requires a named catalog and explicit native id",
            )
        with altered(part_material, "has98", 1), altered(config_material, "has98", 1):
            refused["matching_unqualified_visual_selector"] = refusal(
                lambda: bind(part, cmgr, header), "visual owners disagree or use an unqualified layout",
            )
    return {
        "nodes": {role: metadata(node) for role, node in {
            "header_config": header_node, "manager_config": config_node,
            "manager_visual": config["f78"], "manager_hatch": config["fc48"],
            "part": part.RootValue, "part_visual": model["f78"], "part_hatch": model["f1418"],
            "part_material": model["f1420"], "density_parameter": density, "part_atom": atom,
        }.items()},
        "refusals": refused,
        "solid_atom_id": atom.FieldsValue["f140"],
        "map_counters": {"part": part.MapValue.CounterValue, "manager": cmgr.MapValue.CounterValue,
                         "directory": header.MapValue.CounterValue},
    }


def worker(control, contrasts):
    sys.path.insert(0, str(ROOT / "src"))
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHeader import ReadMgrHeader
    from convert.adapters.solidworks.Archive.Config.Link.ReadModelHead import ReadModelHead
    from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.Materials.BindNamedMat import BindNamedMat
    from convert.adapters.solidworks.Core.TypedResolved.Materials.ReadNamedMat import ReadNamedMat
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    raw = sys.stdin.buffer.read()
    for name in ("ascii", "latin-1", "utf-8", "utf-16", "utf-16-le"):
        lookup(name)
    blocked = []

    def audit(event, _):
        if event in IO_EVENTS:
            blocked.append(event)
            raise RuntimeError("assigned material worker attempted runtime input: " + event)

    sys.addaudithook(audit)
    archive = SldprtArchive.FromBytes(raw)
    results = {"file_sha256": digest(raw), "runtime_file_or_process_accesses": 0}
    if control:
        model = ReadNativeLink(archive, 0).ConfigValue.RootValue
        results["ordinary_read"] = model.ClassValue.NameValue
        results["assignment_refusal"] = refusal(
            lambda: ReadNamedMat(archive), "density is absent, overridden or inconsistent"
        )
    else:
        manager_bytes = archive.Require("Contents/CMgr")
        part_bytes = archive.Require("Contents/Config-0")
        results["ordinary_read"] = refusal(lambda: ReadNativeLink(archive, 0), "unsupported SOLIDWORKS body")
        legacy_manager = refusal(lambda: ReadCmgrMut(manager_bytes, 19000), "unsupported SOLIDWORKS body")
        observation = ReadNamedMat(archive)
        header = ReadModelHead(archive, 19000)
        part = ReadConfigMut(part_bytes, 19000, header, ReadMaterial=True)
        manager = ReadCmgrMut(manager_bytes, 19000, ReadMaterial=True)
        directory = ReadMgrHeader(archive.Require("Contents/CMgrHdr2"), 19000)
        if contrasts:
            results["archive_refusals"] = archive_contrasts(archive, observation, ReadNamedMat)
            results["independent_matching_xml_read"] = True
        results["graph"] = graph_checks(part, manager, directory, BindNamedMat, contrasts)
        require(refusal(lambda: ReadCmgrMut(manager_bytes, 19000), legacy_manager) == legacy_manager,
                "opt-in read changed the default manager grammar")
        results["default_manager_refusal_before_and_after"] = legacy_manager
        results["part_texture_visits"] = part.ReportValue["schema_calls"].get("uoMaterialTextureProperties.restore", 0)
        results["manager_texture_visits"] = manager.ReportValue["schema_calls"].get("uoMaterialTextureProperties.restore", 0)
        if results["part_texture_visits"]:
            results["default_part_refusal_after"] = refusal(
                lambda: ReadConfigMut(part_bytes, 19000, header),
                "unsupported SOLIDWORKS body schema uoMaterialTextureProperties.restore",
            )
        else:
            prior_part = ReadConfigMut(part_bytes, 19000, header)
            require(prior_part.MapValue.CounterValue == part.MapValue.CounterValue, "default part map changed")
            results["default_part_refusal_after"] = None
        results["material_tree_sha256"] = digest(archive.Require(STREAM))
        results["observation"] = asdict(observation)
    require(not blocked, "an embedded reader caught a denied runtime access")
    return results


def native_observations(source):
    life = json.loads(checked(source, "NativeSourcePacket03/Inspection/Result.json", DISCLOSED))
    diag = json.loads(checked(source, "NativeDensityProbe01/Native/Result.json", DIAGNOSTIC))
    entries = {role: life["phases"][role]["states"]["after_save"] for role in ASSIGNED_CASES - {"Diagnostic"}}
    entries = {
        key: {"physical": row["mass"], "configured_name": row["configuration"], **row["part_material"]}
        for key, row in entries.items()
    }
    prior = diag["rows"]["Author"]["states"]["saved"]
    entries["Diagnostic"] = {"physical": prior["selected_mass_property2"], **prior["part_material"]}
    return entries


def check_observation(row, saved, native):
    logged = saved["owners"]
    observation = row["observation"]
    require(observation["PendingDomains"] == ["appearance", "material_tree"], "unqualified domains were dropped")
    require(observation["CatalogValue"] == native["database"] and observation["MaterialName"] == native["material"],
            "typed archive assignment differs from the prior native part-material getter")
    require(observation["DensityValue"] == native["physical"]["density"] == logged["part_density"]["f58"]
            == logged["active_config_density"] and native["physical"]["use_system_units"] is True,
            "typed archive density differs from prior native selected-body density")
    require("configured_name" not in native or observation["CfgName"] == native["configured_name"],
            "typed configuration differs from prior native active configuration")
    require("|".join((observation["CatalogValue"], observation["MaterialName"], str(observation["NativeId"])))
            == logged["active_config_material"], "typed native IdName changed")
    require(row["material_tree_sha256"] == saved["material_tree"]["sha256"], "material XML identity input changed")
    require(row["default_manager_refusal_before_and_after"] == saved["baseline_refusal"],
            "previous named-material compatibility boundary changed")
    require(row["graph"]["map_counters"]["part"] == saved["map_counters"]["configuration"]
            and row["graph"]["map_counters"]["manager"] == saved["map_counters"]["manager"],
            "typed archive map consumption changed")
    require(row["part_texture_visits"] == row["manager_texture_visits"] == logged["manager_texture_calls"],
            "opt-in grammar did not consume the actual texture owner")


def measure(source):
    inputs = load_inputs(source)
    require(set(inputs) == ASSIGNED_CASES, "disclosed assigned-material inventory changed")
    native = native_observations(source)
    logged = json.loads(checked(ROOT, LEDGER + "/AssignedMaterialArchiveOwners01.json", OWNERS))
    control = logged["cases"]["Control"]
    inputs["Control"] = (checked(source, "NativeSourcePacket03/Control.SLDPRT", control["file_sha256"]), control)
    cases = {}
    for role, (raw, row) in inputs.items():
        flags = (("--control",) if role == "Control" else ("--contrasts",) if role == "D01Corner/Author" else ())
        process = run((sys.executable, "-I", "-B", str(HERE), "--worker", *flags),
                      input=raw, capture_output=True, timeout=40, check=False)
        require(process.returncode == 0 and not process.stderr, process.stderr.decode())
        outcome = json.loads(process.stdout)
        require(outcome["file_sha256"] == row["file_sha256"], "custody changed at process boundary")
        if role != "Control":
            check_observation(outcome, row, native[role])
            outcome["observation"].pop("CatalogValue")
            outcome["observation"].pop("MaterialName")
        cases[role] = outcome
    xml = LEDGER + "/AssignedMaterialTreeCorrelation01.json"
    checked(ROOT, xml, CORRELATION_RECEIPT)
    paths = sorted(
        (ROOT / SDK / "Core/TypedResolved/Materials").glob("*.py")
    ) + [ROOT / SDK / part for part in (
        "Archive/Cmgr/ReadCmgrMut.py", "Archive/Config/ReadConfigMut.py", "Archive/Config/Material/BindMatReadMut.py",
    )] + [HERE, CORRELATION]
    return {
        "schema": "kit.sw2026.assigned-material-archive-read.v1",
        "base_commit": BASE, "native_build": "34.5.2.0604",
        "earlier_evidence": {
            "density_diagnostic_sha256": DIAGNOSTIC, "disclosed_lifecycle_sha256": DISCLOSED,
            "archive_owners_sha256": OWNERS, "material_tree_correlation_sha256": CORRELATION_RECEIPT,
        },
        "source_sha256": {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in paths},
        "cases": cases, "fresh_guarded_processes": len(cases),
        "named_assignment_observations": len(cases) - 1,
        "malformed_or_outside_profile_refusals": (
            1 + sum(len(row["graph"]["refusals"]) + len(row.get("archive_refusals", {}))
                    for role, row in cases.items() if role != "Control")
        ),
        "whole_material_semantics_admitted": False, "public_conversion_admitted": False,
        "native_processes_started": 0, "held_out_credit": 0,
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--control", action="store_true")
    parser.add_argument("--contrasts", action="store_true")
    args = parser.parse_args()
    if args.worker:
        sys.stdout.buffer.write(encode(worker(args.control, args.contrasts)))
    else:
        if args.source is None or args.output is None:
            parser.error("--source and --output are required")
        receipt = measure(args.source)
        with args.output.open("xb") as output:
            output.write(encode(receipt))
