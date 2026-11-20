from hashlib import sha256
from json import dumps, loads


# canonical metadata permits independent comparisons without retaining vendor source
def JsonText(Value):
    return dumps(
        Value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


# provenance must bind every collected record to its exact input
def ReadInput(SourcePath):
    if not SourcePath.is_file() or SourcePath.stat().st_size > 128 * 1024 * 1024:
        raise ValueError("Missing or oversized metadata input")
    Content = SourcePath.read_bytes()
    Result = loads(Content)
    if not isinstance(Result, dict) or Result.get("schema_version") != 1:
        raise ValueError("Unsupported metadata input schema")
    return Result, sha256(Content).hexdigest()


# stable identities make independently collected metadata joinable across planner inputs
class CatalogRows:
    # separate registries keep duplicate identities from silently replacing evidence
    def __init__(self):
        self.Sources = {}
        self.Items = {}
        self.Relations = {}
        self.Gaps = {}

    # conflicting provenance invalidates a catalogue before publication
    def AddSource(self, SourceId, Kind, Label, Digest, Details):
        Row = (SourceId, Kind, Label, Digest, JsonText(Details))
        if SourceId in self.Sources and self.Sources[SourceId] != Row:
            raise ValueError("Conflicting source: " + SourceId)
        self.Sources[SourceId] = Row

    # qualified support remains separate from declarations and planning records
    def AddItem(self, ItemId, Kind, Name, SourceId, ParentId=None, Details=None):
        Row = (
            ItemId,
            Kind,
            Name,
            ParentId,
            SourceId,
            JsonText(Details or {}),
            *(["unverified"] * 4),
        )
        if ItemId in self.Items and self.Items[ItemId] != Row:
            raise ValueError("Conflicting item: " + ItemId)
        self.Items[ItemId] = Row

    # typed edges preserve the difference between declared references and inferred matches
    def AddRelation(self, OwnerId, TargetId, Kind, SourceId, Details=None):
        Body = (OwnerId, TargetId, Kind, SourceId, JsonText(Details or {}))
        Identity = sha256(JsonText(Body).encode()).hexdigest()
        self.Relations[Identity] = (Identity, *Body)

    # missing evidence must remain queryable rather than becoming implicit support
    def AddGap(self, Code, SourceId, ItemId=None, Details=None):
        Body = (Code, ItemId, SourceId, JsonText(Details or {}))
        Identity = sha256(JsonText(Body).encode()).hexdigest()
        self.Gaps[Identity] = (Identity, *Body)
