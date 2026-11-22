from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import (
    KLocalBodyStream,
    KResolvedFeaturesStream,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadMgrAtom import (
    ReadMgrAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.brep.Topology.BrepTopology import BrepBody
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordProvenance import ProvenanceSpan


# the imported feature and its physical body occupy different native ownership domains
def AssertLocalIds(
    Feature: FeatureStep,
    BodyValue: DesignBody,
    KernelBody: BrepBody,
    SourceBytes: bytes,
) -> None:
    Archive = SldprtArchive.from_bytes(SourceBytes)
    LinkValue = ReadNativeLink(Archive, 0)
    OwnerId = Feature.attributes["native_object_id"]
    assert isinstance(OwnerId, int)
    NativeOwner = IndexFeatures(LinkValue)[OwnerId]
    assert NativeOwner.ClassValue.NameValue == "moBaseBody_c"
    assert NativeOwner.StartOffset is not None and NativeOwner.EndOffset is not None
    assert Feature.provenance is not None and Feature.provenance.native_id == str(
        OwnerId
    )
    assert Feature.provenance.spans == (
        ProvenanceSpan(
            KResolvedFeaturesStream,
            NativeOwner.StartOffset,
            NativeOwner.EndOffset - NativeOwner.StartOffset,
            "typed-archive-object",
        ),
    )
    AtomValue = ReadMgrAtom(LinkValue)
    assert AtomValue.StartOffset is not None and AtomValue.EndOffset is not None
    assert (
        BodyValue.provenance is not None
        and BodyValue.provenance == KernelBody.provenance
    )
    assert BodyValue.provenance.native_id == f"{KLocalBodyStream}:body:1"
    assert BodyValue.provenance.spans == (
        ProvenanceSpan(
            LinkValue.ConfigName,
            AtomValue.StartOffset,
            AtomValue.EndOffset - AtomValue.StartOffset,
            "typed-native-body-atom",
        ),
        ProvenanceSpan(
            KLocalBodyStream,
            0,
            len(Archive.require(KLocalBodyStream)),
            "native-local-body",
        ),
    )
    ProofValue = CastValue(
        Mapping[str, object], BodyValue.attributes["solidworks.native_body"]
    )
    assert ProofValue == KernelBody.attributes["solidworks.native_body"]
    assert ProofValue["last_modifying_feature_id"] == OwnerId
    assert ProofValue["storage_key"] == Feature.name == BodyValue.name
    assert ProofValue["atom_manager_id"] == AtomValue.FieldsValue["f140"]
    assert ProofValue["atom_body_tag"] == AtomValue.FieldsValue["f180"]
    assert ProofValue["complete_brep_binding"] is True
