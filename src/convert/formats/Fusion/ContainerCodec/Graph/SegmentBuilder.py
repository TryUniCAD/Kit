from convert.formats.Fusion.ContainerCodec.Graph.EmitAuxiliary import EmitAuxiliary
from convert.formats.Fusion.ContainerCodec.Model.AuxiliaryGraph import AuxiliaryGraph
from convert.formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue
from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.formats.Fusion.MetaIndex import SegmentKind


class SegmentBuilder:
    def __init__(
        self,
        Segment: SegmentKind,
        Schemas: tuple[NativeSchema, ...],
        External: EntityProfile,
    ) -> None:
        super().__init__()
        self.Segment = Segment
        self.Schemas = tuple(
            sorted(Schemas, key=lambda Entry: Entry.Value.ClassGuid.upper())
        )
        self.ByName = {Entry.NameValue: Entry for Entry in self.Schemas}
        self.ByGuid = {Entry.Value.ClassGuid.upper(): Entry for Entry in self.Schemas}
        if len(self.ByName) != len(Schemas) or len(self.ByGuid) != len(Schemas):
            raise ValueError("Duplicate Fusion auxiliary schema")
        self.Codes = {
            Entry.Value.ClassGuid.upper(): Index
            for Index, Entry in enumerate(self.Schemas, 256)
        }
        Combined = {Entry.ClassGuid.upper(): Entry for Entry in External.Classes}
        for Entry in self.Schemas:
            Previous = Combined.get(Entry.Value.ClassGuid.upper())
            if Previous is not None and Previous != Entry.Value:
                raise ValueError("Fusion auxiliary and external schemas disagree")
            Combined[Entry.Value.ClassGuid.upper()] = Entry.Value
        self.Profile = EntityProfile(
            External.RootGuid, tuple(Combined.values()), External.ExternalTargets
        )
        self.Records: list[EntityRecord] = []

    def MakeGroups(
        self, ClassName: str, Fields: dict[str, KEntityValue]
    ) -> tuple[EntityGroup, ...]:
        Current = self.ByName[ClassName].Value.ClassGuid.upper()
        Groups: list[EntityGroup] = []
        Consumed: set[str] = set()
        Visited: set[str] = set()
        while Current and Current != self.Profile.RootGuid.upper():
            if Current in Visited or Current not in self.ByGuid:
                raise ValueError("Invalid Fusion auxiliary class ancestry")
            Visited.add(Current)
            Schema = self.ByGuid[Current].Value
            Names = tuple(
                Member.FieldName for Member in Schema.Members if Member.IsSaved
            )
            if not set(Names).issubset(Fields):
                raise ValueError("Missing Fusion auxiliary entity fields")
            Consumed.update(Names)
            Groups.append(
                EntityGroup(
                    Schema.ClassGuid,
                    tuple(
                        NamedValue(NameValue, Fields[NameValue]) for NameValue in Names
                    ),
                )
            )
            Current = Schema.BaseGuid.upper()
        if set(Fields) != Consumed:
            raise ValueError("Unknown Fusion auxiliary entity fields")
        return tuple(Groups)

    def MakeValue(self, ClassName: str, Fields: dict[str, KEntityValue]) -> ValueObject:
        return ValueObject(self.MakeGroups(ClassName, Fields))

    def AddEntity(
        self,
        Identity: int,
        ClassName: str,
        Fields: dict[str, KEntityValue],
        RootName: str = "",
        Subjects: tuple[SubjectValue, ...] = (),
        SplitIndex: int | None = None,
    ) -> None:
        Groups = self.MakeGroups(ClassName, Fields)
        if SplitIndex is not None and not 0 < SplitIndex < len(Groups):
            raise ValueError("Invalid Fusion auxiliary continuation boundary")
        Primary = Groups[:SplitIndex]
        self.Records.append(
            EntityRecord(
                Identity,
                self.Codes[Primary[0].ClassGuid.upper()],
                True,
                EntityFrame(RootName, Subjects or None, None),
                Primary,
            )
        )
        if SplitIndex is not None:
            Following = Groups[SplitIndex:]
            self.Records.append(
                EntityRecord(
                    Identity,
                    self.Codes[Following[0].ClassGuid.upper()],
                    False,
                    EntityFrame(RootName, None, None),
                    Following,
                )
            )

    def Finish(self) -> AuxiliaryGraph:
        return EmitAuxiliary(
            self.Segment, self.Schemas, tuple(self.Records), self.Profile
        )
