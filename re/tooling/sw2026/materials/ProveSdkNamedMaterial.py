from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from io import BytesIO
from json import dumps, loads
from pathlib import Path
from subprocess import run
from tarfile import open as open_tar
from tempfile import TemporaryDirectory
from xml.sax.saxutils import quoteattr
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(HERE.parent))
from NamedMaterialCustody import DIAGNOSTIC_SHA, LIFECYCLE_SHA, digest, disclosed_sources, require

BASE = "c8d85d713dc357770115329e9f1bcb027dbfca4f"
LAYOUT = "convert/adapters/solidworks/Config/RootLayout.json"
MAT_ATTRIBUTE = "solidworks.assigned_part_material"
MATERIALTREE = "swXmlContents/MATERIALTREE"
DOMAINS = "sldprt.material_domains_unresolved"
UNRESOLVED = "sldprt.material_assignment_unresolved"
BLOCKED = {"open", "os.listdir", "os.scandir", "os.system", "os.exec", "os.fork",
           "os.posix_spawn", "os.startfile", "ctypes.dlopen", "subprocess.Popen", "socket.connect"}


def safe_json(data):
    return (dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def make_tree(value, *, density=None, config=None, native_id=None, twice=False):
    catalog = f"{value.CatalogValue}|{value.MaterialName}"
    cfg_name = value.CfgName if config is None else config
    number = value.NativeId if native_id is None else native_id
    density = value.DensityValue if density is None else density
    row = f"<configuration name={quoteattr(cfg_name)} material={quoteattr(f'{catalog}|{value.NativeId}')}/>"
    return (f'<m:materials xmlns:m="http://www.solidworks.com/sldmaterials"><curves/>'
            f'<classification><material name={quoteattr(catalog)} matid="{number}">'
            f'<physicalproperties><DENS value="{density}"/></physicalproperties>'
            f'</material></classification><configurationslist>{row * (2 if twice else 1)}'
            f'</configurationslist></m:materials>').encode("utf-16")


def check_refusals(archive, read, typed):
    from convert.adapters.solidworks.Container.Container import BuildSldprt
    from convert.adapters.solidworks.Container.Format import KPartitionStream
    result = {}
    for role, data in (
        ("wrong_density", make_tree(typed, density=typed.DensityValue + 1)),
        ("wrong_config", make_tree(typed, config=typed.CfgName + " other")),
        ("wrong_id", make_tree(typed, native_id=typed.NativeId + 1)),
        ("duplicate_association", make_tree(typed, twice=True)),
        ("wrong_framing", make_tree(typed).decode("utf-16").encode("utf-8")),
    ):
        corrupted = BuildSldprt(dict(archive.streams) | {MATERIALTREE: data},
                                FormatVersion=archive.format_version)
        messages = []
        for geometry in (False, True):
            document = read(corrupted, geometry)
            require(all(MAT_ATTRIBUTE not in body.attributes for body in document.bodies)
                    and not document.materials, "invalid XML produced a physical assignment")
            outcome, = (entry for entry in document.diagnostics if entry.code == UNRESOLVED)
            messages.append(outcome.message)
        expected = "UTF-16LE framing" if role == "wrong_framing" else "does not corroborate"
        require(messages[0] == messages[1] and expected in messages[0], "wrong XML refusal")
        result[role] = messages[0]
    foreign = BuildSldprt({name: value for name, value in archive.streams.items()
                           if name != KPartitionStream}, FormatVersion=archive.format_version)
    design = read(foreign, False)
    require(not any(MAT_ATTRIBUTE in body.attributes for body in design.bodies),
            "design read attached a material without the physical body")
    outcome, = (entry for entry in design.diagnostics if entry.code == UNRESOLVED)
    require("required stream is missing" in outcome.message, "physical refusal stopped early")
    result["missing_partition"] = outcome.message
    return result


def preserved_digest(document):
    from convert.adapters.solidworks.Core.Adapter import KSourceSemanticShaTwoFive
    from interchange.Core.Common import FreezeMapping
    from interchange.Enums.EnumDocument import Capability

    without = replace(
        document,
        bodies=tuple(replace(body, material_id=None, attributes=FreezeMapping({
            key: item for key, item in body.attributes.items() if key != MAT_ATTRIBUTE
        })) for body in document.bodies),
        materials=(),
        capabilities=document.capabilities - {Capability.KMaterials},
        diagnostics=tuple(item for item in document.diagnostics if item.code not in (DOMAINS, UNRESOLVED)),
        metadata=FreezeMapping({key: item for key, item in document.metadata.items()
                                if key != KSourceSemanticShaTwoFive}),
    )
    return digest(without.to_json().encode("utf-8"))


def worker(source, baseline, control, contrasts):
    src = source.resolve()
    sys.path[:0] = [str(src), str(ROOT)]
    from convert import open_document, write_document
    from convert.adapters.registry.RegistryErrors import NotFoundError
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from interchange import CadDocument
    from interchange.brep.Validation import BrepValidate
    from interchange.document.Models import DocumentProvenance
    from interchange.document.Validation import DocumentFeatureValidate, DocumentReferenceValidate
    if not baseline:
        from convert.adapters.solidworks.Core.TypedResolved.Materials.ReadNamedMat import ReadNamedMat
        if contrasts:
            from convert.adapters.solidworks.Core.TypedResolved.Materials.CheckMatSolid import CheckMatSolid
    data = sys.stdin.buffer.read()
    layout = src / LAYOUT
    layout_sha = digest(layout.read_bytes())
    events = {"grammar": 0, "external": 0}
    active = False
    for name in ("ascii", "latin-1", "cp1252", "utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be"):
        lookup(name)

    def audit(event, args):
        if active and event in BLOCKED:
            if event == "open" and args[0] == str(layout) and args[2] & 3 == 0:
                events["grammar"] += 1
                return
            events["external"] += 1
            raise RuntimeError(f"SDK assigned material accessed external input {event}: {args[0]!r}")

    def read(raw, with_geometry):
        return open_document(raw, source_format="solidworks.sldprt", strict=True,
                             include_brep=with_geometry, include_tessellation=False)

    sys.addaudithook(audit)
    active = True
    try:
        archive = SldprtArchive.from_bytes(data)
        require((MATERIALTREE not in archive.streams) == control, "source role material stream differs")
        documents = {mode: read(data, value) for mode, value in (("geometry", True), ("design", False))}
        geometry, design = documents.values()
        require(geometry.brep is not None and design.brep is None
                and not geometry.validate() and not design.validate(), "public reader changed geometry options")
        body, = geometry.bodies
        other, = design.bodies
        require((body.id, body.final_feature_id) == (other.id, other.final_feature_id), "body identity differs")
        assignment = body.attributes.get(MAT_ATTRIBUTE)
        require(assignment == other.attributes.get(MAT_ATTRIBUTE), "material differs between strict modes")
        declines = {}
        if baseline or control:
            require(assignment is None and all(item.code not in (DOMAINS, UNRESOLVED)
                    for document in documents.values() for item in document.diagnostics),
                    "unassigned or baseline document spuriously gained material")
        else:
            require(assignment is not None and all(
                len(document.materials) == 1
                and document.materials[0].ColorValue is None
                and document.materials[0].id == document.bodies[0].material_id
                and document.materials[0].name == assignment["name"]
                and document.materials[0].Density == assignment["density_kg_m3"]
                and len([item for item in document.diagnostics if item.code == DOMAINS]) == 1
                and all(item.code != UNRESOLVED for item in document.diagnostics)
                for document in documents.values()), "physical record did not preserve unresolved appearance")
            observed = ReadNamedMat(archive)
            require((assignment["native_atom_id"], assignment["native_feature_id"],
                     assignment["native_material_id"], assignment["density_kg_m3"]) ==
                    (observed.AtomId, observed.FeatureId, observed.NativeId, observed.DensityValue),
                    "public fields did not follow their typed owners")
            if contrasts:
                declines = check_refusals(archive, read, observed)
                try:
                    CheckMatSolid(archive, observed.AtomId + 1)
                except ValueError as error:
                    require("partition atom disagrees" in str(error), "incorrect physical identity control")
                    declines["foreign_physical_atom"] = str(error)
                else:
                    raise ValueError("accepted the wrong native solid")
    finally:
        active = False
    require(events["external"] == 0, "a denied read was intercepted")
    if not baseline and not control:
        reopened = CadDocument.from_json(design.to_json())
        require(reopened.bodies[0].attributes[MAT_ATTRIBUTE] == assignment
                and reopened.bodies[0].material_id == design.bodies[0].material_id
                and reopened.materials == design.materials, "neutral JSON lost physical record")
        sink = BytesIO()
        try:
            write_document(design, sink, destination_format="solidworks.sldprt")
        except (NotFoundError, ValueError) as error:
            require(str(error) == "unresolved material assignments cannot be exported",
                    "publication stopped before the unresolved material check")
            declines["material_write"] = str(error)
        else:
            raise ValueError("observed material became authorized native output")
        require(sink.getvalue() == b"", "unsupported writer touched its destination")
    return {
        "file_sha256": digest(data), "grammar_sha256": layout_sha, "grammar_reads": events["grammar"],
        "runtime_external_accesses": events["external"], "unchanged_fields": {
            mode: digest(document.to_json().encode("utf-8")) if control else preserved_digest(document)
            for mode, document in documents.items()
        },
        "assign": None if assignment is None else dict(assignment), "refusals": declines,
    }


def perform(source, baseline_source):
    rows = {}
    for role, raw, measured in disclosed_sources(source):
        control = ("--control",) if measured is None else ()
        extra = ("--contrasts",) if role == "D01Corner/Author" else ()
        runs = []
        for root, flags in ((baseline_source, ("--baseline",)), (ROOT / "src", extra)):
            result = run((sys.executable, "-I", "-B", str(HERE), "--worker", str(root), *control, *flags),
                         input=raw, capture_output=True, timeout=45, check=False)
            require(result.returncode == 0 and not result.stderr, result.stderr.decode("utf-8"))
            runs.append(loads(result.stdout))
        before, after = runs
        require(before["file_sha256"] == after["file_sha256"] == digest(raw)
                and before["grammar_sha256"] == after["grammar_sha256"]
                and before["unchanged_fields"] == after["unchanged_fields"],
                "legacy public semantics changed at " + role)
        if measured is not None:
            assignment = after["assign"]
            require((assignment["catalog"], assignment["name"]) == (measured["database"], measured["material"])
                    and assignment["density_kg_m3"] == measured["density_kg_m3"]
                    and assignment["configuration_name"] == measured["configuration_name"],
                    "public assignment differs from prior independent native measurement")
            assignment = {name: value for name, value in assignment.items() if name not in ("catalog", "name")}
            after["assign"] = assignment
        require(before["runtime_external_accesses"] == after["runtime_external_accesses"] == 0,
                "process tried external I/O")
        rows[role] = after
    return {
        "schema": "kit.sw2026.sdk-assigned-part-material.v1",
        "baseline": BASE, "cases": rows, "fresh_processes": len(rows) * 2,
        "immutable_source_receipts": [LIFECYCLE_SHA, DIAGNOSTIC_SHA],
        "native_build": "34.5.2.0604", "assigned_sources": 7, "strict_assigned_reads": 14,
        "strict_unassigned_controls": 2,
        "tool_sha256": {path.name: digest(path.read_bytes()) for path in
                        (HERE, HERE.with_name("NamedMaterialCustody.py"))},
        "protected_cases": 0, "whole_portable_material": False, "native_write_qualified": False,
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--control", action="store_true")
    parser.add_argument("--contrasts", action="store_true")
    args = parser.parse_args()
    if args.worker:
        sys.stdout.buffer.write(safe_json(worker(args.worker, args.baseline, args.control, args.contrasts)))
    elif args.source and args.output:
        bundle = run(("git", "archive", BASE, "src"), cwd=ROOT, capture_output=True, check=True)
        with TemporaryDirectory(prefix="KitNamedMaterialBaseline-") as scratch:
            with open_tar(fileobj=BytesIO(bundle.stdout)) as archive:
                archive.extractall(scratch, filter="data")
            result = perform(args.source, Path(scratch) / "src")
        with args.output.open("xb") as out:
            out.write(safe_json(result))
        print(digest(args.output.read_bytes()))
    else:
        parser.error("--source and --output are required")
