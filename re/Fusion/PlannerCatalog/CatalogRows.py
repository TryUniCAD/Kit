from hashlib import sha256
from json import dumps, loads


# canonical metadata keeps inventories reproducible without retaining executable vendor source
def JsonText(Value):
    return dumps(
        Value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


# source bounds prevent accidental ingestion of binaries or unbounded external artifacts
def ReadSource(SourcePath):
    if not SourcePath.is_file() or SourcePath.stat().st_size > 32 * 1024 * 1024:
        raise ValueError("Missing or oversized metadata input: " + SourcePath.name)
    return SourcePath.read_bytes()


# shared records enforce identity and provenance before any catalogue files are published
class CatalogRows:
    def __init__(self):
        self.Sources = {}
        self.Items = {}
        self.Relations = {}
        self.Gaps = {}

    def AddSource(self, SourceId, Kind, Label, SourcePath, Version="", Details=None):
        Content = ReadSource(SourcePath)
        Row = (
            SourceId,
            Kind,
            Label,
            sha256(Content).hexdigest(),
            Version,
            JsonText(Details or {}),
        )
        if SourceId in self.Sources and self.Sources[SourceId] != Row:
            raise ValueError("Conflicting source identity: " + SourceId)
        self.Sources[SourceId] = Row
        return Content

    def AddItem(self, ItemId, Kind, Name, SourceId, ParentId=None, Details=None):
        Row = (ItemId, Kind, Name, ParentId, SourceId, JsonText(Details or {}))
        if ItemId in self.Items and self.Items[ItemId] != Row:
            raise ValueError("Conflicting item identity: " + ItemId)
        self.Items[ItemId] = Row
        return ItemId

    def AddRelation(self, OwnerId, TargetId, Relation, SourceId, Details=None):
        Row = (OwnerId, TargetId, Relation, SourceId, JsonText(Details or {}))
        self.Relations[Row] = Row

    def AddGap(self, Code, SourceId, ItemId=None, Details=None):
        Body = (Code, ItemId, SourceId, JsonText(Details or {}))
        GapId = sha256(JsonText(Body).encode()).hexdigest()
        self.Gaps[GapId] = (GapId, *Body)

    def ReadJson(self, SourceId, Kind, SourcePath, RootPath, Version="", Details=None):
        Label = SourcePath.resolve().relative_to(RootPath.resolve()).as_posix()
        Content = self.AddSource(SourceId, Kind, Label, SourcePath, Version, Details)
        Value = loads(Content)
        if not isinstance(Value, dict):
            raise ValueError("Metadata root must be an object: " + Label)
        return Value

    def Validate(self):
        for ItemId, Kind, Name, ParentId, SourceId, Details in self.Items.values():
            if SourceId not in self.Sources or (
                ParentId and ParentId not in self.Items
            ):
                raise ValueError("Dangling item provenance or parent: " + ItemId)
        for OwnerId, TargetId, Relation, SourceId, Details in self.Relations.values():
            if (
                OwnerId not in self.Items
                or TargetId not in self.Items
                or SourceId not in self.Sources
            ):
                raise ValueError("Dangling relation: " + Relation)
        for GapId, Code, ItemId, SourceId, Details in self.Gaps.values():
            if SourceId not in self.Sources or (ItemId and ItemId not in self.Items):
                raise ValueError("Dangling gap: " + Code)
        Dependencies = {}
        Children = {}
        for OwnerId, TargetId, Relation, SourceId, Details in self.Relations.values():
            if Relation == "inherits":
                Dependencies.setdefault(OwnerId, set()).add(TargetId)
                Dependencies.setdefault(TargetId, set())
                Children.setdefault(TargetId, set()).add(OwnerId)
        Ready = [ItemId for ItemId, Parents in Dependencies.items() if not Parents]
        Visited = 0
        while Ready:
            ItemId = Ready.pop()
            Visited += 1
            for ChildId in Children.get(ItemId, ()):
                Dependencies[ChildId].remove(ItemId)
                if not Dependencies[ChildId]:
                    Ready.append(ChildId)
        if Visited != len(Dependencies):
            raise ValueError("API inheritance contains a cycle")
