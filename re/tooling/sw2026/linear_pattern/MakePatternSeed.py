from dataclasses import dataclass

from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import PartBuildInput
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.BindSeedBodyMut import BindSeedBodyMut
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.FrontStockBox import FrontStockBox
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.MakePatternSeed import MakePatternSeed
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.MakeSeedHeaders import MakeSeedHeaders
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.MakeSeedStock import MakeSeedStock
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.ReadStockBox import ReadStockBox
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.SeedStockGraph import SeedStockGraph
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.SeedStockInput import SeedStockInput
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import PartSystem
from convert.adapters.solidworks.Core.Preparation.TwoStock.StockBossGraph import StockBossGraph

from CheckPatternAngleOwners import require


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

    def _shared(self):
        return SeedStockGraph(self.system, self.settings, self.allocator, self.plate, self.seed, self.bounds_m)

    @property
    def roots(self):
        return self._shared().RootsValue

    def headers(self, *later):
        return MakeSeedHeaders(self._shared(), *later)


def box_input(blind):
    return FrontStockBox(blind.sketch, blind.feature, blind.bounds_m)


def stock_input(intent):
    require(type(intent) is RaisedSeedIntent and type(intent.plate) is type(intent.seed) is FrontBlindIntent,
            "expected the modeled Front plate and raised seed")
    return SeedStockInput(intent.name, intent.configuration, intent.path, intent.epoch,
                          box_input(intent.plate), box_input(intent.seed))


def profile_plan(intent, blind):
    box = box_input(blind)
    return MakeSeedStock(stock_input(intent), box, ReadStockBox(box.BoundsValue))


def bind_plate_lineage_mut(root, producer, selected, consumer, result, *, prior=()):
    return BindSeedBodyMut(root, producer, selected, consumer, result, PriorValues=prior)


def make_raised_seed(intent):
    graph = MakePatternSeed(stock_input(intent))
    return RaisedSeedGraph(graph.SystemValue, graph.SettingsValue, graph.Allocator,
                           graph.PlateValue, graph.SeedValue, graph.BoundsValue)
