from dataclasses import replace as ReplaceValue
from io import BytesIO

from pytest import raises as Raises

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.json.Adapter import JsonAdapter
from interchange import CadDocument
from interchange.document.Models.DocumentError import DocumentError
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureStep import FeatureCfgState
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordConfig import Configuration, ParamOverride
from interchange.Records.RecordParameter import ParameterValue
from tests.Interchange.Document.BoundPlaneAxisTests import BuildBoundAxis, ReadAxisDoc


# normal configuration selection must apply inherited and local stations while retaining base data
def CheckCfgExtent() -> None:
    Document = BuildBoundAxis()
    Parent = Configuration(
        "parent",
        "Parent",
        overrides=(AxisOverride("start", 0.7), AxisOverride("end", -1.9)),
    )
    Variant = Configuration(
        "variant",
        "Variant",
        parent_id=Parent.id,
        overrides=(AxisOverride("end", -1.2),),
    )
    Stored = ReplaceValue(
        Document, configurations=(*Document.configurations, Parent, Variant)
    )
    assert ReadAxisDoc(Stored) == (
        SpaceVector(8.0, 18.0, 22.0),
        SpaceVector(8.0, 6.0, 22.0),
    )
    Selected = ReadAxisCfg(Stored, Variant.name)
    assert ReadAxisDoc(Selected) == (
        SpaceVector(8.0, 21.0, 22.0),
        SpaceVector(8.0, 2.0, 22.0),
    )
    assert Selected.parameters == Stored.parameters
    assert Selected.feature_timeline == Stored.feature_timeline


# a suppressed extent is retained without a segment and only selected suppression takes effect
def CheckSuppressed() -> None:
    Document = BuildBoundAxis()
    (StepValue,) = Document.feature_timeline
    Folder = Configuration(
        "suppressed", "Suppressed", suppressed_feature_ids=(StepValue.id,)
    )
    Variant = Configuration(
        "collapsed", "Collapsed", overrides=(AxisOverride("end", 0.4),)
    )
    Feature = ReplaceValue(
        StepValue, configuration_states=(FeatureCfgState("leaf", True),)
    )
    Child = Configuration("leaf", "Leaf", parent_id=Variant.id)
    Stored = ReplaceValue(
        Document,
        configurations=(*Document.configurations, Folder, Variant, Child),
        feature_timeline=(Feature,),
    )
    assert ReadAxisDoc(Stored) == (
        SpaceVector(8.0, 18.0, 22.0),
        SpaceVector(8.0, 6.0, 22.0),
    )
    assert ReadAxisDoc(ReadAxisCfg(Stored, Folder.name)) is None
    assert ReadAxisDoc(ReadAxisCfg(Stored, Child.name)) is None
    with Raises(DocumentError, match="distinct endpoints with a finite span"):
        _ = ReadAxisCfg(Stored, Variant.name)


# selecting an invalid extent value must fail the same length ownership check as ordinary document input
def CheckCfgRefusal() -> None:
    Document = BuildBoundAxis()
    Invalid = ParamOverride("end", ParameterValue(0.5, ValueKind.KAngle, "rad"))
    Variant = Configuration("invalid", "Invalid", overrides=(Invalid,))
    Stored = ReplaceValue(Document, configurations=(*Document.configurations, Variant))
    with Raises(DocumentError, match="requires owned finite length parameters"):
        _ = ReadAxisCfg(Stored, Variant.name)
    Doubled = ReplaceValue(
        Variant, overrides=(AxisOverride("end", -1.0), AxisOverride("end", -1.2))
    )
    Broken = ReplaceValue(Stored, configurations=(*Document.configurations, Doubled))
    with Raises(DocumentError, match="ambiguous configured extent"):
        _ = ReadAxisCfg(Broken, Doubled.name)


# configuration test values intentionally differ from the base unit and value
def AxisOverride(Identity: str, Length: float) -> ParamOverride:
    return ParamOverride(Identity, ParameterValue(Length, ValueKind.KLength, "cm"))


# select the configuration through the ordinary adapter stream boundary
def ReadAxisCfg(Document: CadDocument, SelectionName: str) -> CadDocument:
    return JsonAdapter().read(
        BytesIO(Document.to_json().encode("utf-8")),
        ReadOptions(configuration=SelectionName),
    )
