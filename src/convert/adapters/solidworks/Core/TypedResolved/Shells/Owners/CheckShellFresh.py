from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import (
    KAtomLists,
    KAtomWords,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# fresh configuration metadata selects one live descriptor with no saved body association
def CheckFreshMgr(LinkValue: NativeLink) -> None:
    Manager = LinkValue.ManagerValue
    if Manager is None:
        raise ValueError("fresh shell lacks its linked configuration manager")
    Fields = Manager.RootValue.FieldsValue
    Config = RequireNative(Fields.get("f360"), "moPartConfiguration_c")
    ConfigList = NativeRecord(Fields.get("f370"))
    (ConfigRow,) = NativeRows(ConfigList.get("items"))
    ConfigFields = Config.FieldsValue
    if (
        Fields.get("f658") != 1
        or ConfigList.get("n") != 1
        or Fields.get("f368") is not Config
        or ConfigRow.get("o") is not Config
        or ConfigFields.get("f08") != 0
        or ReadNativeName(Config) != "Default"
        or any(
            not IsLineState(ConfigFields.get(FieldName))
            for FieldName in ("n450", "f450", "n380", "f380", "n3d0", "f3d0")
        )
        or not any(
            Entry.EntryValue is Config and Entry.IndexValue == Config.IndexValue
            for Entry in Manager.MapValue.EntriesValue
        )
    ):
        raise ValueError("fresh shell has alternate configuration or linked body state")


# analytic shell construction requires the ordinary unstamped modifier without alternate selectors
def CheckShellFresh(LinkValue: NativeLink, ShellNode: ArchiveNode) -> None:
    RootFields = LinkValue.ConfigValue.RootValue.FieldsValue
    Fields = ShellNode.FieldsValue
    if (
        RootFields.get("fe38") is not None
        or any(RootFields.get(FieldName) != 0 for FieldName in ("f1010", "f1014"))
        or any(Fields.get(FieldName) is not None for FieldName in ("f6e0", "f758"))
        or Fields.get("f4a0") != 1
        or any(Fields.get(FieldName) != 0 for FieldName in (*KAtomWords, "f7a0"))
        or any(
            not IsLineState(Fields.get(FieldName))
            for FieldName in (*KAtomLists, "f368", "f388", "f780")
        )
    ):
        raise ValueError("fresh shell carries unsupported saved or modifier state")
    CheckFreshMgr(LinkValue)
