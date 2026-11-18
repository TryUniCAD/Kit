from types import MappingProxyType
from collections.abc import Mapping

from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BodyNameGraph import (
    BodyNameGraph,
)


# public body identity evidence must name its actual native domains without fabricated identifiers
def BodyNameProof(GraphValue: BodyNameGraph) -> Mapping[str, object]:
    AtomFields = GraphValue.AtomValue.FieldsValue
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
            "complete_brep_binding": True,
            "qualified_encoding": (
                "printable_ascii"
                if GraphValue.NameValue.isascii()
                else "agreeing_archive_and_implicit_utf16"
            ),
        }
    )
