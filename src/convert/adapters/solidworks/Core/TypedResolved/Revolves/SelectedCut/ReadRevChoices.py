from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadChooserPair import (
    ReadChooserPair,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.ReadRevFace import (
    ReadRevFace,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.RevFaceRef import (
    RevFaceRef,
)


# distinct primary and mirror choosers must repeat the same actual surface objects in order
def ReadRevChoices(
    LinkValue: NativeLink,
    Owner: ArchiveNode,
    Epochs: Mapping[int, int],
    CountValue: int,
) -> tuple[tuple[RevFaceRef, ...], tuple[RevFaceRef, ...]]:
    Primary = ReadChooserPair(LinkValue, Owner, "f4a8")
    Mirror = ReadChooserPair(LinkValue, Owner, "f4c0")
    if len(set((*Primary, *Mirror))) != 4:
        raise ValueError("selected revolve cut chooser repeats a face object")
    First, Second = (
        ReadRevFace(LinkValue, FaceValue, Epochs, CountValue, 0x300)
        for FaceValue in Primary
    )
    FirstMirror, SecondMirror = (
        ReadRevFace(LinkValue, FaceValue, Epochs, CountValue, 0x300)
        for FaceValue in Mirror
    )
    if (First, Second) != (FirstMirror, SecondMirror):
        raise ValueError(
            "selected revolve cut chooser lost its actual mirrored surface ownership"
        )
    return First, Second
