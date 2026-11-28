from collections.abc import Mapping
from types import MappingProxyType

from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ColdOutput import (
    ColdOutput,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId


# computed geometry and actual archive ownership need distinct identity domains in the public evidence
def ColdNameProof(OutputValue: ColdOutput) -> Mapping[str, object]:
    return MappingProxyType(
        {
            "status": "complete",
            "profile": "ordinary_current_cacheless_authored_output_name",
            "configuration_stream": OutputValue.LinkValue.ConfigName,
            "atom_manager_id": OutputValue.AtomValue.FieldsValue["f140"],
            "last_modifying_feature_id": NativeNodeId(OutputValue.BossValue),
            "name_owner": "authored_archive_atom",
            "body_count": 1,
            "complete_brep_binding": True,
            "geometry_source": "typed_parametric_history",
            "native_kernel_identity": False,
            "qualified_encoding": "printable_ascii",
        }
    )
