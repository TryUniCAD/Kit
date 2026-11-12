from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddCornerMut import (
    AddCornerMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddShellMut import (
    AddShellMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.LinkCornerMut import (
    LinkCornerMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.LinkFeatureMut import (
    LinkFeatureMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.LinkTimeline import (
    LinkTimeline,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartCache import PartCache
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.RoofTag import RoofTag
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import ShellSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.SolvePart import SolvePart


def AddPartMut(Author: AuthorState) -> None:
    BaseValue, Stages = SolvePart(Author.SpecValue)
    Solids = (BaseValue, *(Stage.After for Stage in Stages))
    for Index, Stage in enumerate(Stages):
        Prefix = "f" + str(Index + 1) + "_"
        if isinstance(Stage.Feature, ShellSpec):
            Children = AddShellMut(Author, Stage, Prefix, RoofTag(Solids, Index))
        else:
            Children = AddCornerMut(Author, Stage, Prefix)
            LinkCornerMut(Author, Stage, Prefix)
        LinkFeatureMut(Author, Stage, Prefix, Children)
    LinkTimeline(Author, Stages)
    Author.Change("body", cache=PartCache(Author, Solids[-1]))
