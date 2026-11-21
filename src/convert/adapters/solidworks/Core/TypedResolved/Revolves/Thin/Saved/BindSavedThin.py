from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BindBodyName import (
    BindBodyName,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BodyNameProof import (
    BodyNameProof,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BodyNameSource import (
    BodyNameSource,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.CheckBrepOwners import (
    CheckBrepOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.BindThinDoc import (
    BindThinDoc,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.BuildThinGeom import (
    BuildThinGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.Saved.CheckThinBrep import (
    CheckThinBrep,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.Saved.ReadSavedThin import (
    ReadSavedThin,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.Saved.ReadThinCache import (
    ReadThinCache,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument


# a matched native body retains its partition bytes and publishes the typed editable definition
def BindSavedThin(
    Document: CadDocument, Archive: SldprtArchive, LinkValue: NativeLink
) -> CadDocument:
    (ConfigValue,) = Document.configurations
    (BodyValue,) = Document.bodies
    if not ConfigValue.active:
        raise ValueError(
            "SOLIDWORKS saved thin does not own the selected configuration"
        )
    OwnerValue = ReadSavedThin(LinkValue, Archive, ConfigValue.name)
    GraphValue, PhysicalValue = ReadThinCache(
        Document, Archive, LinkValue, OwnerValue.SweepValue.NodeValue
    )
    if BodyValue.final_feature_id != f"sldprt:feature:{GraphValue.FeatureId}":
        raise ValueError(
            "SOLIDWORKS saved thin body has an unresolved producing feature"
        )
    CheckBrepOwners(PhysicalValue, BodyValue.id)
    SectorValue = BuildThinGeom(OwnerValue, BodyValue.id)
    CheckThinBrep(PhysicalValue, SectorValue.BrepValue)
    BoundValue = BindThinDoc(Document, LinkValue, OwnerValue)
    DesignValue = ReplaceValue(BoundValue.bodies[0], topology=SectorValue.TopologyValue)
    BoundValue = ReplaceValue(BoundValue, bodies=(DesignValue,))
    if BoundValue.brep is not None:
        return BindBodyName(BoundValue, GraphValue)
    ProofValue = BodyNameProof(GraphValue, HasBrep=False)
    return ReplaceValue(
        BoundValue,
        bodies=(
            ReplaceValue(
                DesignValue,
                name=GraphValue.NameValue,
                provenance=BodyNameSource(GraphValue),
                attributes=FreezeMapping(
                    {**DesignValue.attributes, "solidworks.native_body": ProofValue}
                ),
            ),
        ),
        metadata=FreezeMapping(
            {**BoundValue.metadata, "solidworks.native_body_names": ProofValue}
        ),
    )
