from dataclasses import dataclass, replace
from ntpath import basename, splitext

from convert.adapters.solidworks.Archive.Construction.BodyScope.MakeBodyRef import MakeBodyRef
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import SetCfgStampMut
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Header.MakeRootLog import MakeRootLog
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import MakePartHeaders
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import PartBuildInput
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import PartSystem
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughStock import ThroughStock
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.TwoStock.MakeStockBoss import MakeStockBoss
from convert.adapters.solidworks.Core.Preparation.TwoStock.StockBossGraph import StockBossGraph
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadCutAtomId import ReadCutAtomId

from CheckPatternAngleOwners import require
from PatternHingeGeometry import box_points, joined_front_bounds


@dataclass(frozen=True, slots=True)
class FrontBlindIntent:
    sketch: str
    feature: str
    bounds_m: tuple[tuple[float, float, float], tuple[float, float, float]]


@dataclass(frozen=True, slots=True)
class RaisedSeedIntent:
    name: str
    configuration: str
    path: str
    epoch: int
    plate: FrontBlindIntent
    seed: FrontBlindIntent


@dataclass(frozen=True, slots=True)
class RaisedSeedGraph:
    system: PartSystem
    settings: PartBuildInput
    allocator: PersistentIds
    plate: StockBossGraph
    seed: StockBossGraph
    bounds_m: tuple[tuple[float, float, float], tuple[float, float, float]]

    @property
    def roots(self):
        return (*self.system.FeatureValues, self.plate.ProfileValue.ProfileValue, self.plate.FeatureValue,
                self.seed.ProfileValue.ProfileValue, self.seed.FeatureValue)

    def headers(self, *later):
        headers = MakePartHeaders(self.system, self.settings, self.allocator)
        owners = self.plate.FeatureValue, self.seed.FeatureValue, *later
        for header in headers[:2]:
            logs = header.FieldsValue["f20"].FieldsValue
            logs["items"] = (*logs["items"], *(MakeRootLog(owner, self.settings.HeaderValue) for owner in owners))
        return headers


def profile_plan(intent, blind):
    (x0, y0, _), (x1, y1, z1) = box_points(blind.bounds_m)
    vertices = (x0, y0), (x1, y0), (x1, y1), (x0, y1)
    return ThroughStock(
        intent.name, intent.configuration, "Front Plane", blind.sketch, blind.sketch, blind.feature, blind.feature,
        f"D1@{blind.feature}", f"Body@{blind.feature}", vertices, z1, x1 - x0, y1 - y0, "z"
    )


def bind_plate_lineage_mut(root, producer, selected, consumer, result, *, prior=()):
    base = prior[-1][0] if prior else producer
    lineage = ((producer, selected), *prior)
    atoms = tuple(atom for _, atom in lineage)
    ids = tuple(ReadCutAtomId(atom, feature) for feature, atom in lineage)
    output_id = ReadCutAtomId(result, consumer)
    managed = root.FieldsValue["fd88"]
    current = tuple(row["o"] for row in managed["atoms"])
    fields = consumer.FieldsValue
    require(
        len(prior) <= 1 and len(set((*ids, output_id))) == len(ids) + 1
        and current == (*reversed(atoms), result) and managed["n6c"] == len(current)
        and managed["f260"] == output_id and tuple(atom.FieldsValue["f144"] for atom in current) == (1,) * len(prior) + (0, 0)
        and all(feature.FieldsValue["owner"] is root for feature, _ in (*lineage, (consumer, result)))
        and all(feature.FieldsValue["f528"]["items"][0]["o"] is atom
                for feature, atom in (*lineage, (consumer, result)))
        and not fields["has_f530"] and not fields["has_f548"],
        "cannot consume a crossed, reused or non-current raised-seed atom"
    )
    wrapper = MakeBodyRef(root, base, selected)
    wrapper.FieldsValue.update(n110=len(ids), f110=[{"v": identity} for identity in ids])
    fields.update(f544=1, has_f548=1, f548={"n": 1, "items": [{"o": wrapper}]}, has_f530=1,
                  f530={"n": 1, "items": [{"o": selected}]})
    selected.FieldsValue["f144"] = 1
    return wrapper


def make_raised_seed(intent):
    require(type(intent) is RaisedSeedIntent and type(intent.plate) is type(intent.seed) is FrontBlindIntent,
            "expected the modeled Front plate and raised seed")
    labels = (intent.name, intent.configuration, intent.plate.sketch, intent.plate.feature, intent.seed.sketch, intent.seed.feature)
    require(all(type(label) is str and label and label.isprintable() for label in labels)
            and type(intent.path) is str and splitext(basename(intent.path)) == (intent.name, ".SLDPRT")
            and type(intent.epoch) is int and 0 < intent.epoch < 0x7FFFFFFF,
            "raised seed needs explicit part, profile, operation and lifecycle identities")
    bounds = joined_front_bounds(intent.plate.bounds_m, intent.seed.bounds_m)
    plate, seed = profile_plan(intent, intent.plate), profile_plan(intent, intent.seed)
    settings = replace(MakePartRecipe(plate, intent.epoch), OutputValue=SelfFileInput(intent.path, intent.epoch))
    system_labels = tuple(name for _, name in (*settings.SystemValue.FolderValues, *settings.SystemValue.PlaneNames))
    identities = (settings.SystemValue.CabinetName, settings.SystemValue.OriginName, *system_labels, *labels[2:])
    require(len(set(identities)) == len(identities), "raised seed operation and support names must be distinct")
    allocator = PersistentIds()
    system = MakePartBaseMut(settings, plate, allocator)
    manager = system.RootValue.FieldsValue["fd88"]
    plate_graph = MakeStockBoss(system, settings, plate, allocator, manager, False)
    seed_graph = MakeStockBoss(system, settings, seed, allocator, manager, True)
    plate_graph.FeatureValue.FieldsValue["f544"] = 1
    bind_plate_lineage_mut(system.RootValue, plate_graph.FeatureValue, plate_graph.AtomValue,
                           seed_graph.FeatureValue, seed_graph.AtomValue)
    SetCfgStampMut(system.ConfigValues[0], allocator)
    return RaisedSeedGraph(system, settings, allocator, plate_graph, seed_graph, bounds)
