from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Native.Circular.RimPolicy.ReadRimContext import (
    ReadRimContext,
)
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Models.SnapshotModel import SnapshotModel
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField
from tests.Convert.Integration.Fusion.RimFillet.Geometry.FindRimSlot import FindRimSlot
from tests.Convert.Integration.Fusion.RimFillet.Geometry.ChangeRimNode import (
    ChangeRimNode,
)
from tests.Convert.Integration.Fusion.RimFillet.Geometry.ChangeRimRecipe import (
    ChangeRimRecipe,
)


# full archive mutations retain all unaffected source records for meaningful fail closed integration coverage
def ChangeRimModel(Model: DocumentModel, CaseName: str) -> DocumentModel:
    if CaseName in ("selected_lower", "adjacent_faces"):
        return ChangeRimRecipe(Model, CaseName)
    Context = ReadRimContext(BuildGraph(Model))
    if CaseName == "history_end":
        return ChangeField(
            Model,
            Context.Feature.ObjectId,
            "endModelHS",
            Context.Feature.Fields["startModelHS"],
        )
    if CaseName == "snapshot_height":
        PartValue = Model.Snapshots[0]
        Snapshot = PartValue.Snapshot
        assert isinstance(Snapshot, SnapshotModel)
        return ReplaceData(
            Model,
            Snapshots=(
                ReplaceData(
                    PartValue,
                    Snapshot=ReplaceData(
                        Snapshot,
                        Model=ReplaceData(
                            Snapshot.Model, Height=Snapshot.Model.Height * 1.01
                        ),
                    ),
                ),
            ),
        )
    History = Model.Bodies[0].History
    assert isinstance(History, JournalModel)
    if CaseName == "history_scale":
        return ReplaceData(
            Model,
            Bodies=(
                ReplaceData(
                    Model.Bodies[0],
                    History=ReplaceData(
                        History,
                        Header=ReplaceData(
                            History.Header, Scale=History.Header.Scale * 1.1
                        ),
                    ),
                ),
            ),
        )
    Index, ReferenceId = FindRimSlot(Model, CaseName)
    Entities = tuple(
        ChangeRimNode(Entity, CaseName, ReferenceId) if Ordinal == Index else Entity
        for Ordinal, Entity in enumerate(History.Entities)
    )
    return ReplaceData(
        Model,
        Bodies=(
            ReplaceData(
                Model.Bodies[0], History=ReplaceData(History, Entities=Entities)
            ),
        ),
    )
