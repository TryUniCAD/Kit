from collections.abc import Mapping

from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from interchange.Core.Common import FreezeMapping


# the native comparison owns the original and each of the two independently saved edits
def ReadSwHashes(Value: object) -> Mapping[str, object]:
    Owners = ReadMeasMap(Value)
    if set(Owners) != {"original", "section", "path"}:
        raise ValueError("sweep measurement lacks the independent comparisons")
    Hashes = {RoleValue: ReadMeasSha(Digest) for RoleValue, Digest in Owners.items()}
    if len(set(Hashes.values())) != len(Hashes):
        raise ValueError("sweep measurement repeats an independent comparison")
    return FreezeMapping(Hashes)
