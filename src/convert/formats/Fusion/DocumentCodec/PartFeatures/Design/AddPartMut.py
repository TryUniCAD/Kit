from convert.formats.Fusion.DocumentCodec.Materials.LinkMaterialMut import (
    LinkMaterialMut,
)
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Construct.AddWorkMut import (
    AddWorkMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddCornerMut import (
    AddCornerMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddShellMut import (
    AddShellMut,
    ShellTags,
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
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.RoofTag import (
    CapTagSet,
    RoofTagSet,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddExtrudeFeat import (
    AddExtrudeFeat,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Hole.AddHoleMut import (
    AddHoleMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Hole.HoleRoot import RoofMiddle
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.AxisSpec import AxisSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.HoleSpec import HoleSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircularSpec import (
    CircularSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MirrorSpec import (
    MirrorSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import PlaneSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PointSpec import PointSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import ShellSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.AddCopyMut import (
    AddCopyMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.RevolveSpec import (
    RevolveSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.AddPlaneMut import (
    AddPlaneMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MoveSpec import MoveSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Move.AddMoveMut import AddMoveMut
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.OffsetSpec import (
    OffsetSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.DraftSpec import DraftSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Draft.AddDraftMut import (
    AddDraftMut,
    DraftTags,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Offset.AddOffsetMut import (
    AddOffsetMut,
    OffsetPick,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Revolve.AddRevolveFeat import (
    AddRevolveFeat,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.SolvePart import SolvePart


def AddStageMut(
    Author: AuthorState,
    Stage: PartStage,
    Prefix: str,
    Context: tuple[tuple[PrismSolid, ...], int, tuple[PartStage, ...]],
) -> list[str]:
    Solids, Place, Stages = Context
    Feature = Stage.Feature
    if isinstance(Feature, ShellSpec):
        return AddShellMut(Author, Stage, Prefix, ShellTags(Solids, Place, Stage))
    if isinstance(Feature, HoleSpec):
        Middle = RoofMiddle(Stages, Stage)
        return AddHoleMut(
            Author, Stage, Prefix, (RoofTagSet(Solids, Place + 1), Middle)
        )
    if isinstance(Feature, PlaneSpec):
        return AddPlaneMut(Author, Stage, Prefix)
    if isinstance(Feature, (AxisSpec, PointSpec)):
        return AddWorkMut(Author, Stage, Prefix)
    if isinstance(Feature, MoveSpec):
        return AddMoveMut(Author, Stage, Prefix)
    if isinstance(Feature, OffsetSpec):
        return AddOffsetMut(Author, Stage, Prefix, OffsetPick(Solids, Place, Stage))
    if isinstance(Feature, DraftSpec):
        return AddDraftMut(Author, Stage, Prefix, DraftTags(Solids, Place, Stage))
    if isinstance(Feature, (PatternSpec, CircularSpec, MirrorSpec)):
        Source = Stages[Feature.SourceIndex].Feature
        IsRoof = isinstance(Feature, PatternSpec) or isinstance(Source, HoleSpec)
        TagSet = CapTagSet(Solids, Place + 1, IsRoof)
        return AddCopyMut(Author, Stage, Prefix, TagSet)
    Children = AddCornerMut(Author, Stage, Prefix)
    LinkCornerMut(Author, Stage, Prefix)
    return Children


def AddPartMut(Author: AuthorState) -> None:
    BaseValue, Stages = SolvePart(Author.SpecValue)
    Solids = (() if BaseValue is None else (BaseValue,)) + tuple(
        Stage.After for Stage in Stages
    )
    Offset = 0 if BaseValue is not None else -1
    for Index, Stage in enumerate(Stages):
        Prefix = "f" + str(Index + 1) + "_"
        if isinstance(Stage.Feature, (ExtrudeSpec, RevolveSpec)):
            Builder = AddExtrudeFeat
            if isinstance(Stage.Feature, RevolveSpec):
                Builder = AddRevolveFeat
            Builder(Author, Stage, Prefix)
            continue
        Context = (Solids, Index + Offset, Stages)
        Children = AddStageMut(Author, Stage, Prefix, Context)
        LinkFeatureMut(Author, Stage, Prefix, Children)
    LinkTimeline(Author, Stages)
    if BaseValue is None:
        LinkMaterialMut(Author)
    Author.Change("body", cache=PartCache(Author, Solids[-1]))
