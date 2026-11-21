from types import MappingProxyType
from collections.abc import Mapping

from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BodyNameGraph import (
    BodyNameGraph,
)


# public body identity evidence must name its actual native domains without fabricated identifiers
def BodyNameProof(
    GraphValue: BodyNameGraph, *, HasBrep: bool = True
) -> Mapping[str, object]:
    AtomFields = GraphValue.AtomValue.FieldsValue
    if GraphValue.LocalStoreKey is not None:
        return MappingProxyType(
            {
                "status": "complete",
                "profile": "current_single_local_solid_names",
                "configuration_stream": GraphValue.LinkValue.ConfigName,
                "local_body_stream": GraphValue.StreamName,
                "storage_key": GraphValue.LocalStoreKey,
                "body_transmit_index": GraphValue.TreeValue.BodyIndex,
                "atom_manager_id": AtomFields["f140"],
                "atom_body_tag": AtomFields["f180"],
                "last_modifying_feature_id": GraphValue.FeatureId,
                "name_owner": GraphValue.LocalNameOwner,
                "body_count": 1,
                "complete_brep_binding": HasBrep,
                "qualified_encoding": (
                    "printable_ascii"
                    if GraphValue.NameValue.isascii()
                    else "agreeing_archive_and_implicit_utf16"
                ),
            }
        )
    return MappingProxyType(
        {
            "status": "complete",
            "profile": "ordinary_current_single_solid_names",
            "configuration_stream": GraphValue.LinkValue.ConfigName,
            "partition_stream": GraphValue.StreamName,
            "body_transmit_index": GraphValue.TreeValue.BodyIndex,
            "atom_manager_id": AtomFields["f140"],
            "body_match_tag": AtomFields["f180"],
            "last_modifying_feature_id": GraphValue.FeatureId,
            "name_owner": (
                "authored_atom_and_kernel"
                if GraphValue.IsAuthored
                else "implicit_kernel"
            ),
            "body_count": 1,
            "complete_brep_binding": HasBrep,
            "qualified_encoding": (
                "printable_ascii"
                if GraphValue.NameValue.isascii()
                else "agreeing_archive_and_implicit_utf16"
            ),
        }
    )
