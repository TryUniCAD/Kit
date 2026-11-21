from argparse import ArgumentParser
from base64 import b64encode
from dataclasses import replace
from hashlib import sha256
from math import degrees, isclose
from pathlib import Path, PureWindowsPath
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path[:0] = [str(path) for path in (ROOT / "src", HERE.parent, HERE.parent.parent / "PrincipalWriter",
                                      HERE.parent.parent / "EndModes", HERE.parents[2])]

from AuditRevEndOwners import guard_runtime
from AuthorRevolveFamilies import STOCK_SKETCHES
from ProveTwoDirectionRevolves import warm
from RevolveFamilyModel import PROFILE, STOCK_NAMES, FEATURE_NAMES, cut_predictions
from StockCutFixture import DESIGNS, fixture
from StockCutGeometry import cut_measure
from StockCutPlan import neutral_projection, require
from convert.adapters.solidworks.Archive.Construction.BodyScope.BindStockMut import BindStockMut
from convert.adapters.solidworks.Archive.Construction.BodyScope.MakeBodyRef import MakeBodyRef
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import SetCfgStampMut
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordConfig import KeywordConfig
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import KeywordDim
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import KeywordFeature
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeywords import MakeKeywords
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import MakePartHeaders
from convert.adapters.solidworks.Archive.Construction.Revolves.Feature.MakeRevFeatMut import MakeRevFeatMut
from convert.adapters.solidworks.Archive.Construction.Revolves.Part.EmitRevStreams import EmitRevStreams
from convert.adapters.solidworks.Archive.Construction.Revolves.Sketch.MakeRevProfMut import MakeRevProfMut
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import MakePartDef
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import KResolvedFeaturesStream, KeywordsStream
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockAtom import ReadStockAtom
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadManagedCutAtoms import ReadCutAtoms
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import ReadSingleNode
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevCore import ReadRevCore


POLICIES = ("producer", "sentinel")
VERSION = 19000


def digest(raw):
    return sha256(raw).hexdigest()


def model(locator):
    name = PureWindowsPath(locator).stem
    design = DESIGNS[0] | {"name": name}
    base = fixture(design)
    features = tuple(replace(value, name=label)
                     for value, label in zip(base.feature_timeline, (*STOCK_NAMES, FEATURE_NAMES["cut"]), strict=True))
    sketches = tuple(replace(value, name=label)
                     for value, label in zip(base.sketches, (*STOCK_SKETCHES, PROFILE), strict=True))
    bodies = tuple(replace(value, name=label)
                   for value, label in zip(base.bodies, (STOCK_NAMES[1], FEATURE_NAMES["cut"]), strict=True))
    document = replace(base, feature_timeline=features, sketches=sketches, bodies=bodies)
    case = {"name": name, "family": "cut", "split": "discovery", "plane": design["plane"],
            "axis_x_m": design["axis"] * 0.001, "axis_axial_m": [value * 0.001 for value in design["span"]],
            "axial_m": [value * 0.001 for value in design["axial"][2]],
            "radius_m": [value * 0.001 for value in design["radial"][2]],
            "stock_radii_m": [[value * 0.001 for value in limits] for limits in design["radial"][:2]],
            "stock_axial_m": [value * 0.001 for value in design["axial"][0]],
            "angle_deg": design["angle"], "edit_angle_deg": 119.25, "reverse": False, "scope": "inner"}
    return document, case, design["epoch"]


def keywords(system, profiles, features, plan, epoch):
    config = tuple(KeywordConfig(FieldInt(node.FieldsValue, "f08"), ReadNodeName(node), "")
                   for node in system.ConfigValues)
    public = tuple(KeywordFeature(FieldInt(node.FieldsValue, "f08"), ReadNodeName(node),
                                 node.ClassValue.NameValue, "Feature", (), (), None, None)
                   for node in system.FeatureValues)
    formed = tuple(KeywordFeature(FieldInt(node.FieldsValue, "f08"), ReadNodeName(node),
                                 "Cut-Revolve" if index == 2 else "Revolve", "Feature",
                                 (KeywordDim("D1", degrees(op.AngleValue), "degree"),), (), None, None)
                   for index, (node, op) in enumerate(zip(features, plan.operations, strict=True)))
    sketches = tuple(KeywordFeature(FieldInt(node.FieldsValue, "f08"), ReadNodeName(node),
                                   None, "Sketch", (), (), True, None) for node in profiles)
    return MakeKeywords(plan.operations[0].NameValue, epoch, config, (*public, *formed, *sketches))


def build(locator, policy):
    require(policy in POLICIES, "unknown scoped revolve reference mode")
    document, case, epoch = model(locator)
    plan = neutral_projection(document)
    first = plan.operations[0]
    inputs = replace(MakePartRecipe(first, epoch), OutputValue=SelfFileInput(locator, epoch))
    CheckPartInput(document, inputs, first, tuple(name for op in plan.operations[1:]
                                                 for name in (op.SketchName, op.FeatureName)))
    allocator = PersistentIds()
    system = MakePartBaseMut(inputs, first, allocator)
    profiles, features, atoms = [], [], []
    for index, operation in enumerate(plan.operations):
        profile, axis = MakeRevProfMut(system, inputs, operation, allocator)
        feature, _, _, _ = MakeRevFeatMut(system, profile, axis, inputs, operation, allocator, IsCut=index == 2)
        feature.FieldsValue.update(f870=int(index != 1), f544=1)
        profiles.append(profile.ProfileValue)
        features.append(feature)
        if index < 2:
            atoms.append(BindStockMut(system.RootValue.FieldsValue["fd88"], feature, AppendMember=True))
    selected = plan.selected_index
    wrapper = MakeBodyRef(system.RootValue, features[selected], atoms[selected])
    if policy == "sentinel":
        wrapper.FieldsValue["f108"] = -1
    features[-1].FieldsValue.update(has_f548=1, f548={"n": 1, "items": [{"o": wrapper}]})
    roots = (*system.FeatureValues, *(node for pair in zip(profiles, features, strict=True) for node in pair))
    SetCfgStampMut(system.ConfigValues[0], allocator)
    headers = MakePartHeaders(system, inputs, allocator)
    definition = MakePartDef(inputs.DefinitionValue, inputs.DensityValue)
    streams, config, resolved = EmitRevStreams(system, roots, headers, definition, inputs, plan.operations[2])
    streams[KeywordsStream] = keywords(system, profiles, features, plan, epoch)
    return BuildSldprt(streams, FormatVersion=4), streams, case, plan, resolved.ContextValue


def inspect(raw, streams, context, plan, policy):
    archive = SldprtArchive.from_bytes(raw)
    require(len(streams) == 10 and all(archive.require(key) == value for key, value in streams.items()),
            "generated native container stream membership differs")
    config_header = ReadHeaderGraph(archive.require("Contents/Config-0-ModelHeader"), VERSION)
    cfg_key = "Contents/Config-0"
    config = ReadConfigMut(archive.require(cfg_key), VERSION, config_header)
    resolved = ReadResolvedMut(archive.require(KResolvedFeaturesStream), VERSION, config.MapValue, context)
    link = NativeLink(config, resolved, "Default", KResolvedFeaturesStream)
    require(len(resolved.RootsValue) == 23 and config.MapValue.CounterValue == resolved.MapBase,
            "two-stock part root count or inherited base differs")
    roots = resolved.RootsValue[-6:]
    profiles, features = roots[::2], roots[1::2]
    for profile, feature, code, item in zip(profiles, features, (1, 0, 1), plan.operations, strict=True):
        owner = ReadRevCore(link, feature, profile, IndexFeatures(link), code)
        require(owner.EndValue.AgainstValue is None and owner.AngleValue.NameValue == "D1"
                and owner.AngleValue.RadiansValue == item.AngleValue and not owner.IsReverse,
                "generated part lost an active angular driver")
    atoms = tuple(ReadStockAtom(node, False) for node in features[:2])
    require(set(atoms) == ReadCutAtoms(link)
            and all(atom.FieldsValue["f144"] == atom.FieldsValue["f180"] == atom.FieldsValue["f1b0"] == 0 for atom in atoms),
            "native regeneration requires two actual live cold stock atoms")
    cut = features[2].FieldsValue
    wrapper = ReadSingleNode(cut["f548"], "moCompSolidBody_c")
    fields = wrapper.FieldsValue
    selected = plan.selected_index
    atom = atoms[selected].FieldsValue["f140"]
    producer = features[selected].FieldsValue["f08"]
    base = producer if policy == "producer" else -1
    require(cut["f544"] == cut["has_f548"] == 1 and cut["has_f528"] == cut["has_f530"] == cut["has_f4a8"]
            == cut["has_f4c0"] == fields["f100"] == fields["f104"] == 0 and fields["ff0"] is None
            and fields["f18"] == fields["f1c"] == atom and fields["f110"] == [{"v": atom}]
            and fields["f108"] == base and fields["f58"].FieldsValue["owner"] is config.RootValue,
            "candidate contains an unresolved or unintended selector, output atom or face cache")
    require(archive.require(cfg_key) == WriteConfigMut(config.RootValue, VERSION, config_header)[0]
            and archive.require(KResolvedFeaturesStream) == WriteResolMut(
                resolved.RootsValue, resolved.ExtraFields, VERSION, config.MapValue, context)[0],
            "generated selectors did not exactly re-emit their linked archives")
    return {"selector": {"f18": atom, "f108": base, "producer_id": producer,
                         "f110": [atom], "f100": 0, "f104": 0, "ff0": None},
            "resolved_key": KResolvedFeaturesStream, "active_root_count": 23,
            "config_counter": config.MapValue.CounterValue, "resolved_counter": resolved.MapValue.CounterValue,
            "streams": {key: {"sha256": digest(value), "bytes": len(value)} for key, value in streams.items()}}


def worker(request):
    warm()
    blocked = guard_runtime()
    raw, streams, case, plan, context = build(request["locator"], request["policy"])
    proof = inspect(raw, streams, context, plan, request["policy"])
    untouched, changed = cut_measure(plan)
    predicted = cut_predictions(case)
    for name, measured in zip((STOCK_NAMES[1], STOCK_NAMES[0]), (untouched, changed), strict=True):
        wanted = predicted[name]
        require(all(isclose(value, target, rel_tol=1e-12, abs_tol=1e-16) for value, target in zip(
            (measured.volume_m3, measured.area_m2, *measured.centre_m),
            (wanted["volume_m3"], wanted["area_m2"], *wanted["com_m"]), strict=True)),
            "independent angular geometry predictions differ")
    require(not blocked and not any(name in ("Swapp", "pythoncom", "pywintypes") or name.startswith("win32com")
                                   for name in sys.modules), "generation used host files or a CAD runtime")
    return {"case": case, "sha256": digest(raw), "bytes": len(raw), "zero_runtime_reads": True, **proof,
            "data": b64encode(raw).decode("ascii")}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true", required=True)
    parser.parse_args()
    print(json.dumps(worker(json.load(sys.stdin)), allow_nan=False))
