from pytest import mark as MarkTests, raises as Raises

from convert import open_document as OpenDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Convert.Api.Fusion.SavedCuboid.ChangeSnapOwner import ChangeSnapOwner
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource


# the public reader must reject typed snapshots attached to the wrong native roles
@MarkTests.parametrize(
    ("RoleName", "Rejection"),
    (
        ("history_owner", "serializer ownership is not reciprocal"),
        ("snapshot_owner", "serializer ownership is not reciprocal"),
        ("serializer", "rBRepSerializer references an incompatible class"),
        ("part_name", "not the selected serializer part"),
        ("scope_asset", "cache scope disagrees with its component"),
        ("root_id", "passive identities disagree with its roots"),
        ("missing_part", "requires exactly one typed prism snapshot"),
        ("extra_part", "requires exactly one typed prism snapshot"),
        ("root_with_extra", "requires exactly one typed prism snapshot"),
    ),
)
def TestSnapOwner(RoleName: str, Rejection: str) -> None:
    Source = SavedSource(KSavedCases[0]).read_bytes()
    assert (
        OpenDocument(Source, source_format="f3d").metadata["fusion.read_only"] is True
    )
    Original = ReadDocument(Source)
    Changed = ChangeSnapOwner(Original, RoleName)
    assert Changed != Original
    Payload = EmitParsed(Changed)
    assert ReadDocument(Payload) == Changed
    with Raises(ValueError, match=Rejection):
        _ = OpenDocument(Payload, source_format="f3d")
