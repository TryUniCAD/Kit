from convert.adapters.Fusion.Native.Graph.GraphValues import MappingItems
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


# duplicate map keys must refuse before dictionary lookup could hide an extra source owner
def ReadRimMap(Value: KEntityValue) -> dict[KEntityValue, KEntityValue]:
    Entries = MappingItems(Value)
    Result = {Entry.First: Entry.Second for Entry in Entries}
    if len(Result) != len(Entries):
        raise ValueError("Native rim map contains duplicate source identities")
    return Result
