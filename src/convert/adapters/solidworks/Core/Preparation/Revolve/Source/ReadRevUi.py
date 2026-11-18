from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import (
    ModelDefSettings,
)
from convert.adapters.solidworks.Archive.Definition.Construction.RequireDefNumber import (
    RequireDefNumber,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Core.Preparation.Revolve.Source.RevSourceUi import (
    RevSourceUi,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# existing model definition inputs may be recovered from their actual source owners without treating the independent complete detail graph as equivalent presentation
def ReadRevUi(GraphValue: ModelDefGraph) -> RevSourceUi:
    if type(GraphValue) is not ModelDefGraph or GraphValue.VersionValue != 19000:
        raise ValueError(
            "source revolve ui requires a complete version 19000 Definition"
        )
    FieldsValue = RequireNative(GraphValue.DocumentValue, "uiPartDoc_c").FieldsValue
    StandardValue = RequireNative(FieldsValue.get("fba8"))
    Notebook = NativeRecord(FieldsValue.get("ffd8"))
    Journal = ArchiveNode.RequireNode(Notebook.get("f18"))
    if Journal.ClassValue != RuntimeClass("uoJournal_c", 0):
        raise ValueError("source revolve ui requires its concrete journal owner")
    JournalName = Journal.FieldsValue.get("f08")
    if type(JournalName) is not str:
        raise ValueError("source revolve ui requires its actual journal name")
    LowValue = FieldInt(FieldsValue, "fad8_0")
    HighValue = FieldInt(FieldsValue, "fad8_1")
    if any(not -(1 << 31) <= Value < (1 << 31) for Value in (LowValue, HighValue)):
        raise ValueError("source revolve ui display words exceed signed native width")
    MaskValue = (LowValue & 0xFFFFFFFF) | ((HighValue & 0xFFFFFFFF) << 32)
    OptimalValue = FieldInt(FieldsValue, "fa64")
    PreferenceValue = FieldInt(FieldsValue, "fa90")
    if OptimalValue not in (0, 1) or PreferenceValue not in (0, 1):
        raise ValueError(
            "source revolve ui switches exceed their recovered boolean domain"
        )
    DensityValue = RequireDefNumber(FieldsValue.get("f1688"))
    if DensityValue <= 0:
        raise ValueError("source revolve ui density must be positive")
    return RevSourceUi(
        ModelDefSettings(
            StandardValue.ClassValue.NameValue,
            tuple(
                IndexValue for IndexValue in range(64) if MaskValue & (1 << IndexValue)
            ),
            (
                FieldInt(FieldsValue, "fa58"),
                FieldInt(FieldsValue, "fa5c"),
                FieldInt(FieldsValue, "fa60"),
                bool(OptimalValue),
            ),
            bool(PreferenceValue),
            JournalName,
            19000,
        ),
        DensityValue,
    )
