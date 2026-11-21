from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import (
    SetCfgStampMut,
)
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import (
    MakePartBaseMut,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.BindSeedBodyMut import (
    BindSeedBodyMut,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.CheckSeedInput import (
    CheckSeedInput,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.JoinSeedBounds import (
    JoinSeedBounds,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.MakeSeedStock import (
    MakeSeedStock,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.ReadStockBox import (
    ReadStockBox,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.SeedStockGraph import (
    SeedStockGraph,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.SeedStockInput import (
    SeedStockInput,
)
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.TwoStock.MakeStockBoss import (
    MakeStockBoss,
)


# the linear pattern needs an actual merged front seed on one managed solid
def MakePatternSeed(InputValue: SeedStockInput) -> SeedStockGraph:
    NamesValue = CheckSeedInput(InputValue)
    PlateBounds = ReadStockBox(InputValue.PlateValue.BoundsValue)
    SeedBounds = ReadStockBox(InputValue.SeedValue.BoundsValue)
    BoundsValue = JoinSeedBounds(PlateBounds, SeedBounds)
    PlatePlan = MakeSeedStock(InputValue, InputValue.PlateValue, PlateBounds)
    SeedPlan = MakeSeedStock(InputValue, InputValue.SeedValue, SeedBounds)
    SettingsValue = ReplaceValue(
        MakePartRecipe(PlatePlan, InputValue.SavedAt),
        OutputValue=SelfFileInput(InputValue.PathValue, InputValue.SavedAt),
    )
    TreeInput = SettingsValue.SystemValue
    AllNames = (
        TreeInput.CabinetName,
        TreeInput.OriginName,
        *(Label for _, Label in (*TreeInput.FolderValues, *TreeInput.PlaneNames)),
        *NamesValue,
    )
    if len(set(AllNames)) != len(AllNames):
        raise ValueError("raised seed operation and support names must be distinct")
    Allocator = PersistentIds()
    SystemValue = MakePartBaseMut(SettingsValue, PlatePlan, Allocator)
    Manager = SystemValue.RootValue.FieldsValue.get("fd88")
    if not isinstance(Manager, dict):
        raise ValueError("raised seed requires the actual root atom manager")
    ManagerValue = CastValue(dict[str, object], Manager)
    PlateValue = MakeStockBoss(
        SystemValue, SettingsValue, PlatePlan, Allocator, ManagerValue, False
    )
    SeedValue = MakeStockBoss(
        SystemValue, SettingsValue, SeedPlan, Allocator, ManagerValue, True
    )
    PlateValue.FeatureValue.FieldsValue["f544"] = 1
    _ = BindSeedBodyMut(
        SystemValue.RootValue,
        PlateValue.FeatureValue,
        PlateValue.AtomValue,
        SeedValue.FeatureValue,
        SeedValue.AtomValue,
    )
    SetCfgStampMut(SystemValue.ConfigValues[0], Allocator)
    return SeedStockGraph(
        SystemValue, SettingsValue, Allocator, PlateValue, SeedValue, BoundsValue
    )
