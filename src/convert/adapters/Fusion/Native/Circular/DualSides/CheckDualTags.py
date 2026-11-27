from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.adapters.Fusion.Native.Circular.DualSides.ReadDualLabel import (
    ReadDualLabel,
)
from convert.adapters.Fusion.Native.Rectangle.CurveTags import CurveTag
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag


# every physical side cap and rim requires its exact owning feature groups
def CheckDualTags(
    State: GeometryState,
    Shape: CircleShape,
    Operations: tuple[int, ...],
    Primary: str,
    FirstMm: float,
    SecondMm: float,
) -> None:
    SeenOwners: set[int] = set()
    Roles: set[str] = set()
    Owned = (Operations[0],)
    Curve = str(CurveTag(Shape.CurveNode))
    for Entity in State.Entities:
        if not isinstance(Entity, TagAttrib):
            continue
        if Entity.Attribute != -1 or Entity.Links.OwnerRef in SeenOwners:
            raise ValueError(
                "Native dual sides contain extended or duplicate feature tags"
            )
        SeenOwners.add(Entity.Links.OwnerRef)
        if isinstance(State.Entities[Entity.Links.OwnerRef], BodyNode):
            continue
        RoleName = ReadDualLabel(State, Entity.Links.OwnerRef, FirstMm, SecondMm)
        Expected = (
            (FeatureTag(Primary, (Operations[int(RoleName == "second")],)),)
            if RoleName in ("first", "second")
            else (
                (FeatureTag("1" if RoleName == "lower" else "2", Owned),)
                if RoleName in ("lower", "upper")
                else (
                    (FeatureTag("-" + Curve, Owned), FeatureTag(Curve, Owned))
                    if RoleName == "joint"
                    else (FeatureTag("-1", Owned),)
                )
            )
        )
        if RoleName in Roles or Entity.Groups != Expected:
            raise ValueError(
                "Native dual side feature tag disagrees with its physical owner"
            )
        Roles.add(RoleName)
    if len(SeenOwners) != 8 or Roles != {
        "first",
        "second",
        "lower",
        "upper",
        "rim_lower",
        "joint",
        "rim_upper",
    }:
        raise ValueError("Native dual side tags do not cover every physical owner")
