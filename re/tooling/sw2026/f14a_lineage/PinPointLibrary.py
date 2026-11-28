from hashlib import sha256
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve()
SW = HERE.parent.parent
sys.path.insert(0, str(SW / "materials"))

from MaterialPe import PeImage

LIBRARY = "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"
CLASSES = (
    ("moRefPoint_c", 0x4DAF46F0, 0x4D175328, 0x4C2FC170, 0x730),
    ("moRefPointData_c", 0x4DAF6AF8, 0x4D177BF0, 0x4C2FC010, 0x10),
    ("moTwoAxisRefPointData_c", 0x4DAF6B88, 0x4D177F20, 0x4C2FC4B0, 0x20),
)
AXIS_VTABLE = 0x4D1571B0
SHARED_DISPATCH = {
    0x3E8: 0x4BB2A650,
    0x3F8: 0x4C03E170,
    0x4B8: 0x4C17A7B0,
    0x4C0: 0x4C17B570,
}
ROUTES = {
    "fixed_root_constructor": 0x4C2F7BB0,
    "data_constructor": 0x4C2FCCF0,
    "base_reference_geometry_constructor": 0x4C2CE5D0,
    "owner_obtaining_atom_feature_constructor": 0x4B6FEEC0,
    "fixed_root_serialize": 0x4C2FC170,
    "base_reference_geometry_serialize": 0x4C276B00,
    "base_point_data_serialize": 0x4C2FC010,
    "coincident_reference_axis_pair_serialize": 0x4C2FC4B0,
    "lightweight_coordinate_data_serialize": 0x4C2FBFB0,
    "geometry_getter": 0x4C2F8EB0,
    "get_updated_points": 0x4C2F9190,
    "geometry_data_update": 0x4C2F9390,
    "db_tail": 0x4C03C560,
}
IMPORTS = (
    0x4CD3D870, 0x4CD3D878, 0x4CD3D890, 0x4CD3D898,
    0x4CD3D990, 0x4CD328A0, 0x4CD3A940, 0x4CD3A948, 0x4CD3A590,
)


def audit(path):
    image = PeImage(path)
    assert image.sha256 == LIBRARY and image.base == 0x4B140000
    exports = {row["name"]: row["address"] for row in image.exports()}
    assert exports["??0moRefPoint_c@@QEAA@AEBVmgPoint_c@@PEAVmoConcept_c@@_N@Z"] == hex(ROUTES["fixed_root_constructor"])
    assert exports["?getPoint@moRefPoint_c@@QEBAXAEAVmgPoint_c@@@Z"] == hex(ROUTES["geometry_getter"])
    assert exports["?getUpdatedPoints@moRefPoint_c@@QEAAHAEAVmgPoint_c@@PEAVmoUpdateEngine_c@@N@Z"] == hex(ROUTES["get_updated_points"])
    assert exports["?getNameLocation@moRefGeom_c@@UEBAAEBVmgPoint_c@@XZ"] == "0x4c2ce9b0"
    assert exports["?setNameLocation@moRefGeom_c@@QEAAXAEBVmgPoint_c@@@Z"] == "0x4c2cf0c0"
    classes = {}
    for name, descriptor, vtable, serializer, size in CLASSES:
        index = image.offset(descriptor)
        assert image.string(image.u64(index)) == name
        assert image.u32(index + 8) == size
        assert image.u32(index + 12) == 0x80000001
        assert image.u64(image.offset(vtable + 0x28)) == serializer
        classes[name] = {
            "descriptor": hex(descriptor), "instance_bytes": size, "schema": 1,
            "versionable": True, "vtable": hex(vtable), "serializer_slot": "0x28",
            "serializer": hex(serializer),
        }
    fixed_vtable = CLASSES[0][2]
    getter = image.u64(image.offset(fixed_vtable + 0x20C8))
    assert getter == 0x4C2CE9B0
    for slot, target in SHARED_DISPATCH.items():
        assert target == image.u64(image.offset(fixed_vtable + slot))
        assert target == image.u64(image.offset(AXIS_VTABLE + slot))
    no_update = image.u64(image.offset(CLASSES[1][2] + 0xA8))
    assert no_update == 0x4B27CBE0
    ranges = [image.pin(name, *image.range(address)) for name, address in ROUTES.items()]
    ranges.extend((
        image.pin("point_coordinate_accessor_leaf", getter, getter + 8),
        image.pin("point_coordinate_setter_leaf", 0x4C2CF0C0, 0x4C2CF0CE),
        image.pin("fixed_data_has_no_projected_update", no_update, no_update + 3),
    ))
    imports = image.imports()
    return {
        "pe_sha256": image.sha256, "preferred_base": hex(image.base),
        "serialize_catalogue_sha256": sha256(
            (HERE.parents[4] / "re/data/Serialization/SerializeMap2026.json").read_bytes()
        ).hexdigest(),
        "classes": classes, "ranges": ranges,
        "imports": {hex(key): imports[key] for key in IMPORTS},
        "axis_vtable": hex(AXIS_VTABLE),
        "common_point_and_axis_dispatch": {hex(slot): hex(target) for slot, target in SHARED_DISPATCH.items()},
        "fixed_data_update_virtual_slot": "0xa8",
        "geometry_accessor_virtual_slot": "0x20c8",
        "geometry_accessor": hex(getter),
        "static_prepared_without_version_19000_vendor_record": True,
    }


if __name__ == "__main__":
    print(json.dumps(audit(Path(sys.argv[1])), sort_keys=True, indent=2))
