from hashlib import sha256 as CalcSha
from ntpath import join as JoinPath
from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Header.ReadFileTable import GetFileRef
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.Writing.Chamfers.CheckPairDrive import (
    CheckPairDrive,
)
from convert.adapters.solidworks.Core.Writing.Chamfers.PairBatch import PairBatch


# exact publication needs the same complete bytes and actual cold feature and self locator
def MatchPairCase(Batch: PairBatch, Candidate: PartCandidate, WrittenAt: int) -> int:
    Digest = CalcSha(Candidate.BytesValue).hexdigest()
    Slots = tuple(
        Index
        for Index, RowValue in enumerate(Batch.Generated)
        if RowValue.get("archive_sha256") == Digest
    )
    if len(Slots) != 1:
        raise ValueError(
            "regenerated distance chamfer has no unique exact native measurement"
        )
    (SlotValue,) = Slots
    BuildValue = Batch.Generated[SlotValue]
    Header = ReadHeaderGraph(
        Candidate.StreamsValue["Contents/Config-0-ModelHeader"],
        Candidate.ConfigValue.VersionValue,
    )
    SelfValue = GetFileRef(Header.FieldsValue["f38"])
    Feature = RequireNative(Candidate.ResolvedValue.RootsValue[-1], "Chamfer_c")
    NameValue = BuildValue.get("name")
    if (
        type(NameValue) is not str
        or PureWindowsPath(SelfValue.PathValue).name != NameValue
        or SelfValue.PathValue != JoinPath(Batch.Destination, NameValue)
        or type(BuildValue.get("archive_bytes")) is not int
        or BuildValue.get("archive_bytes") != len(Candidate.BytesValue)
        or Header.FieldsValue.get("f70") != WrittenAt
        or BuildValue.get("mode_word") != FieldInt(Feature.FieldsValue, "f8c0")
    ):
        raise ValueError(
            "distance chamfer measurement does not match its generated scope or locator"
        )
    CheckPairDrive(Batch.Cases[SlotValue], SlotValue, ReadNodeName(Feature))
    return SlotValue
