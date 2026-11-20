from argparse import ArgumentParser
from codecs import lookup
from contextlib import contextmanager
from dataclasses import dataclass, replace
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import sys

from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import FeatureInstant
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import PartTextInput
from convert.adapters.solidworks.Archive.Construction.Part.Imports.MakeBareImport import MakeBareImport
from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import LightInput
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Transform import KTransformIdentity
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit


ROOT = Path(__file__).resolve().parents[4]
IMPORTS = "src/convert/adapters/solidworks/Archive/Construction/Part/Imports"
RESEARCH = "re/tooling/sw2026/imported_body_source"
RECEIPTS = "re/solidworks/measurements/2026"
LIT_RECEIPT = f"{RECEIPTS}/GeneratedLocalBodyPartCompleted01.json"
UNLIT_RECEIPT = f"{RECEIPTS}/GeneratedLocalImportWithoutLight01.json"
LIT_PATH = PureWindowsPath(r"C:\KitImportedProbe03\Candidates")
UNLIT_PATH = PureWindowsPath(r"C:\KitImportedProbe04\Candidates")
EXPECTED_LIGHT_STREAMS = {
    "Header2", "Contents/Config-0-ModelHeader", "Contents/Config-0",
    "Contents/CMgr", "Contents/Config-0-ResolvedFeatures",
}


@dataclass(frozen=True)
class BareLabels:
    NameValue: str
    ConfigName: str
    FeatureName: str
    PlaneName: str = "Front Plane"
    AxisValue: str = "z"
    SketchName: str = ""


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fingerprint(value):
    return {"bytes": len(value), "sha256": sha256(value).hexdigest()}


def recipe(labels, destination, epoch, properties=None):
    return replace(MakePartRecipe(labels, epoch), OutputValue=SelfFileInput(str(destination), epoch),
                   PropertiesValue=properties)


@contextmanager
def guard_build():
    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    audit.BeginBuild()
    enabled = True

    def audit_hook(event, arguments):
        if enabled:
            audit.InspectEvent(event, arguments)
            if event.startswith("socket.") or event == "ctypes.dlopen":
                raise PermissionError("bare import construction attempted " + event)

    sys.addaudithook(audit_hook)
    try:
        yield audit
    finally:
        enabled = False
    require(not audit.DeniedReads, "bare import attempted runtime file access")


def verify_graph(result, labels):
    system = result.SystemValue
    feature = result.FeatureValue
    active, top, _ = result.HeadersValue
    entries = system.RootValue.FieldsValue["fd88"]["atoms"]
    require(len(entries) == 1 and feature is result.ResolvedValue.RootsValue[-1]
            and system.RootValue is result.ConfigValue.RootValue, "candidate lost its actual shared part roots")
    atom = entries[0]["o"]
    require(feature.FieldsValue["local_storage_key"] == labels.FeatureName
            and feature.FieldsValue["f528"]["items"][0]["o"] is atom
            and feature.FieldsValue["f498"] == [{"v": result.AtomId}]
            and atom.FieldsValue["f140"] == result.AtomId
            and atom.FieldsValue["f12c"] == atom.FieldsValue["f130"] == feature.FieldsValue["f08"],
            "local feature lost its selected part atom")
    require(active.FieldsValue["f40"] == top.FieldsValue["f40"] == system.ConfigValues[0].FieldsValue["f860"]
            and active.FieldsValue["f44"] == top.FieldsValue["f44"]
            and system.ConfigValues[0].FieldsValue["f6f8"] == 1,
            "completed update lost its active body or header stamps")
    for header in (active, top):
        model_log, import_log = header.FieldsValue["f20"].FieldsValue["items"]
        require(model_log.FieldsValue["f48"] == system.RootValue.FieldsValue["f08"]
                and import_log.FieldsValue["f48"] == feature.FieldsValue["f08"]
                and import_log.FieldsValue["f50"].TextValue == labels.FeatureName,
                "header import log lost its actual feature or model")


def package_control():
    require("BuildImportedLocalPart" not in sys.modules and
            not any(name == "para" or name.startswith("para.") for name in sys.modules),
            "standalone probe loaded research construction")
    points = tuple(PlaneVector(*point) for point in ((1., -3.), (20., -5.), (14., 7.)))
    profile = tuple(LineGeometry(a, b) for a, b in zip(points, points[1:] + points[:1], strict=True))
    solid, *_ = BuildPrism("bare-package-control", KTransformIdentity, profile, 3., 17.)
    body, = solid.bodies
    model = replace(solid, bodies=(replace(body, design_body_id=""),))
    document = CadDocument(CadSource("kit.neutral", "", ""), (Configuration("active", "Working", True),),
                           (), (), (), (), (), (), brep=model)
    dest = PureWindowsPath(r"C:\Kit\StandaloneBare\Component.SLDPRT")
    labels = BareLabels(dest.stem, "Working", "Imported shell Δ")
    settings = recipe(labels, dest, 1790000000)
    for codec in ("ascii", "latin-1", "utf-8", "utf-16-le"):
        lookup(codec)
    with guard_build() as audit:
        result = MakeBareImport(document, settings, labels)
        verify_graph(result, labels)
    require("BuildImportedLocalPart" not in sys.modules, "standalone construction invoked research code")
    return {"part": fingerprint(result.BytesValue), "streams": len(result.StreamsValue),
            "runtime_input_reads": len(audit.DeniedReads), "research_builder_imports": 0}


def ambient_input(light, epoch):
    return LightInput("ambient", light.NameValue, light.ExternalName, light.AmbientValue,
                      light.DiffuseValue, light.SpecularValue, light.ColourValue,
                      True, False, True, 1., True, 16., None, None, FeatureInstant(epoch, 0))


def compare_part(builder, document, destination, light, semantics=None):
    config, = document.configurations
    label = builder.DEFAULT_FEATURE_NAME if semantics is None else semantics.feature_name
    labels = BareLabels(destination.stem, config.name, label)
    settings = recipe(labels, destination, builder.EPOCH, None if semantics is None else semantics.properties)
    raw, streams = builder.make_part(document, str(destination), "Bare", completed=True, semantics=semantics)
    base_document = document if light is None else replace(document, metadata={})
    actual = MakeBareImport(base_document, settings, labels, AmbientValue=light)
    verify_graph(actual, labels)
    require((actual.BytesValue, actual.StreamsValue) == (raw, streams),
            "package part differs from its same path research counterpart")
    measured = builder.verify_part(actual.BytesValue, actual.StreamsValue)
    return {"part": fingerprint(actual.BytesValue), "streams": measured["streams"],
            "graph": {key: measured[key] for key in ("feature", "feature_id", "atom_id", "kernel_nodes")}}


def lit_and_unlit(builder, lit_record, unlit_record):
    rows = {}
    light = ambient_input(builder.AUTHORED_AMBIENT, builder.EPOCH)
    for shape, (points, levels, _) in builder.CASES.items():
        case = shape + "Bare"
        filename = case + ".SLDPRT"
        lit_document = builder.make_document(shape, points, levels, builder.AUTHORED_AMBIENT)
        bare_document = builder.make_document(shape, points, levels, None)
        lit = compare_part(builder, lit_document, LIT_PATH / filename, light)
        unlit = compare_part(builder, bare_document, UNLIT_PATH / filename, None)
        same_path_bare = compare_part(builder, bare_document, LIT_PATH / filename, None)
        prior_lit = lit_record["cases"][case]
        prior_unlit = unlit_record["cases"][case]
        require(lit["part"] == {"bytes": prior_lit["generated_bytes"], "sha256": prior_lit["native_input_sha256"]}
                and lit["streams"] == prior_lit["generated_streams"]
                and prior_lit["initial_diagnostics"]["warning"] == 0,
                "completed authored light bytes no longer match their measured oracle input")
        require(unlit["part"]["sha256"] == prior_unlit["generated_sha256"]
                and prior_unlit["open_error"] == 0 and prior_unlit["open_warning"] == 32,
                "completed empty environment bytes no longer match their measured oracle input")
        changes = {name for name in lit["streams"].keys() | same_path_bare["streams"].keys()
                   if lit["streams"].get(name) != same_path_bare["streams"].get(name)}
        require(changes == EXPECTED_LIGHT_STREAMS, "authored light touched an unrelated stream")
        rows[case] = {"authored_ambient": lit, "empty_environment": unlit,
                      "same_path_empty_environment": same_path_bare,
                      "same_path_light_differences": sorted(changes),
                      "prior_native_open_status": {"authored_ambient": 0, "empty_environment": 32}}
    return rows


def rejects(document, labels, settings, light):
    cases = {
        "unowned_metadata": (replace(document, metadata={"native_scene": "unknown"}), settings, labels, None, "unowned neutral document fields"),
        "unmatched_config": (document, settings, replace(labels, ConfigName="Other config"), None, "configuration differs"),
        "invalid_config_id": (replace(document, configurations=(replace(document.configurations[0], id=12),)),
                              settings, labels, None, "configuration differs"),
        "nonneutral_units": (replace(document, units="inch"), settings, labels, None, "neutral millimetre B-rep"),
        "competing_active_metadata": (replace(document, configurations=(replace(document.configurations[0], attributes={"properties": {"x": "y"}}),)),
                                      settings, labels, None, "configuration differs"),
        "boss_setting": (document, replace(settings, SelectedLeader=1), labels, None, "no boss presentation owner"),
        "wrong_extension": (document, replace(settings, OutputValue=replace(settings.OutputValue, PathName=str(PureWindowsPath(settings.OutputValue.PathName).with_suffix(".SLDASM")))),
                            labels, None, "extension differs"),
        "duplicate_feature_name": (document, settings, replace(labels, FeatureName=labels.PlaneName), None, "distinct authored names"),
        "directional_light": (document, settings, labels, replace(light, KindValue="directional", DirectionValue=(1., 0., 0.), ShadowSoftness=0.), "typed authored ambient light"),
        "crossed_light_owner": (document, settings, labels, replace(light, NameValue=labels.FeatureName), "distinct authored names"),
        "property_formula": (document, replace(settings, PropertiesValue=PartTextInput({}, {"Finish": "=1+1"}, {})), labels, None, "literal unlinked"),
        "untyped_property_bag": (document, replace(settings, PropertiesValue=PartTextInput([], {}, {})), labels, None, "typed literal property bags"),
    }
    readings = {}
    for name, (model, values, names, ambient, diagnostic) in cases.items():
        try:
            MakeBareImport(model, values, names, AmbientValue=ambient)
        except (TypeError, ValueError) as error:
            require(diagnostic in str(error), f"wrong refusal for {name}: {error}")
            readings[name] = str(error)
        else:
            raise ValueError("unqualified application state went through bare import: " + name)
    return readings


def compare_text(builder):
    points, levels, _ = builder.CASES["Rectangular"]
    document = builder.make_document("part-text", points, levels, None)
    config, = document.configurations
    config = replace(config, name="Working Δ")
    document = replace(document, configurations=(config,))
    flags = PartTextInput({"title": "Independent text"}, {"Finish": "As cut"}, {"Finish": "Fixture 17"})
    semantics = builder.ImportedPartSemantics("Local prism Δ", "Local prism Δ", False, config.name, flags)
    destination = LIT_PATH / "BareText.SLDPRT"
    measured = compare_part(builder, document, destination, None, semantics)
    labels = BareLabels(destination.stem, config.name, semantics.feature_name)
    settings = recipe(labels, destination, builder.EPOCH)
    return measured, rejects(document, labels, settings, ambient_input(builder.AUTHORED_AMBIENT, builder.EPOCH))


def measure():
    standalone = package_control()
    import BuildImportedLocalPart as builder

    lit_bytes = (ROOT / LIT_RECEIPT).read_bytes()
    unlit_bytes = (ROOT / UNLIT_RECEIPT).read_bytes()
    paths = (
        *(f"{IMPORTS}/{name}.py" for name in ("BindImportScene", "BindImportMut", "CheckBareImport", "FinishImportMut",
                                              "ImportCandidate", "LogImportMut", "MakeBareImport", "MakeImportKeys", "ReadImportScene")),
        f"{RESEARCH}/BuildImportedLocalPart.py", f"{RESEARCH}/VerifyBareImportPackage.py",
        "src/convert/adapters/solidworks/Archive/Construction/System/Members/MakeLightMut.py",
        "src/convert/adapters/solidworks/Archive/Construction/Part/EmitPartArchive.py",
        "src/convert/adapters/solidworks/Archive/Construction/Part/CheckPartInput.py",
        "src/convert/adapters/solidworks/Archive/Construction/Part/MakePartBaseMut.py",
        "src/convert/adapters/solidworks/Archive/Construction/Part/MakePartHeaders.py",
        "src/convert/adapters/solidworks/Archive/Partition/ImportHistory/MakeImportHist.py",
        "src/convert/adapters/solidworks/Archive/Partition/LocalPrism/MakeLocalPrism.py",
        "src/convert/adapters/solidworks/Archive/Partition/LocalWrite/EncodeLocalBody.py",
        "src/convert/adapters/solidworks/Container/Format.py",
    )
    digests = {path: sha256((ROOT / path).read_bytes()).hexdigest() for path in paths}
    digests.update({LIT_RECEIPT: sha256(lit_bytes).hexdigest(), UNLIT_RECEIPT: sha256(unlit_bytes).hexdigest()})
    lit, unlit = json.loads(lit_bytes), json.loads(unlit_bytes)
    with guard_build() as audit:
        compared = lit_and_unlit(builder, lit, unlit)
        text_case, refusals = compare_text(builder)
    return {"schema": "kit.sw2026.bare-import-package.v1", "standalone_package": standalone,
            "prior_authored_ambient_path": str(LIT_PATH), "prior_empty_environment_path": str(UNLIT_PATH),
            "compared_parts": compared, "literal_text_part": text_case, "refusals": refusals,
            "owning_code_and_prior_evidence_sha256": digests,
            "comparison_denied_io_events": len(audit.DeniedReads),
            "input_saved_parts": 0, "guest_launches": 0, "heldout_reads": 0, "public_writer_changes": 0}


if __name__ == "__main__":
    parser = ArgumentParser(description="Compare the generated package bare import with known research and native input digests")
    parser.add_argument("--package-only", action="store_true")
    arguments = parser.parse_args()
    result = package_control() if arguments.package_only else measure()
    print(json.dumps(result, indent=2, sort_keys=True))
