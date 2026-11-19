from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from json import dumps
from pathlib import PureWindowsPath
from sys import addaudithook
from uuid import NAMESPACE_URL, uuid5

from Classes import registry
from builders.Part import construct_part
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileText
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from downstream.CheckCollectorProjection import collector_body
from downstream.CheckFaceOperands import read_operands
from downstream.Components import read_component_body, write_component_body
from downstream.PrismFaceConstructors import prism_face_constructor_fields
from downstream.Storage import ConfigurationCache, cache_path, store_part_caches
from para.DownstreamIds import allocate_fresh_downstream, owned_solid_chains
from para.Partition import read_partition
from para.concentric.CylinderFace import words
from para.rectangle.ArchiveAttachment import FeatureUpdate, archive_for_oracle
from para.rectangle.CheckAttachment import neutral_request
from para.rectangle.CheckProjection import schedule
from para.rectangle.Geometry import plan_rectangle
from para.rectangle.RectangleAttributes import Appearance
from para.rectangle.RectanglePartition import complete_topology, project_rectangle


def authored_prism(variant, classes, *, model_path=None, model_second=None, allocate_downstream=True,
                   later_body_updates=1):
    name = f"PrismFaceConstructors{variant}"
    path = PureWindowsPath(f"C:/KitResearch/{name}.SLDPRT" if model_path is None else model_path)
    if not path.is_absolute() or path.suffix.casefold() != ".sldprt":
        raise ValueError("native prism construction needs an actual absolute part path")
    limits = (2.375 * variant, -7.125, 32.25 + variant, 11.875, 6.25 + 1.75 * variant)
    second = 1818197000 + 243 * variant if model_second is None else model_second
    fraction = 833710 * variant
    request = neutral_request(path, limits, modified_at=second)
    session = schedule(1492 + 318 * variant, 24, 1, 0, 5, 2, later_body_updates, second, fraction)
    events = (
        FeatureUpdate(1, second, fraction // 5, False),
        FeatureUpdate(4, second, fraction // 3, True),
        FeatureUpdate(8, second, fraction // 2, True),
    )
    child = construct_part(registry=classes, native_plane_roles=True, **request)
    plan = plan_rectangle(child, session)
    appearance = Appearance((113, 54, 192), 0.125, request["document"]["density_kg_m3"])
    allocation = None
    if allocate_downstream:
        topology, _ = complete_topology(plan.topology)
        faces, edges = owned_solid_chains(topology)
        owner = uuid5(NAMESPACE_URL, "urn:kit:solidworks:downstream:face-constructor:" + name)
        allocation = allocate_fresh_downstream(faces, edges, owner, second, fraction, is_assembly=False)
    projection = project_rectangle(child, plan, appearance, downstream=allocation)
    streams = archive_for_oracle(registry=classes, child=child, plan=plan, projection=projection,
                                 session=session, feature_updates=events)
    return path, SldprtArchive.from_bytes(BuildSldprt(streams, FormatVersion=4)), allocation


def check_graph(readback, archive, path):
    partition = read_partition(archive.require(KPartitionStream))
    nodes = {item.index: item for item in partition.nodes}
    body, = (item for item in partition.nodes if item.kind == 12)
    atom, = words(nodes, body, "ATOM_ID_2001", 1)
    identifiers, expected = read_operands(partition)
    kernel_keys = {number: words(nodes, nodes[face], "FACE_ID_2001", 2) for face, number in identifiers.items()}
    file_owners = []
    units = []
    representations = []
    lookup = {"moEndFaceSurfIdRep_c": 40, "moFromSktEntSurfIdRep_c": 74}
    rows = readback.FieldsValue["f48"]
    assert [row["word"] for row in rows] == sorted(expected)
    for row in rows:
        outer = row["object"].FieldsValue
        assert outer["f18"] == outer["f1c"] == atom
        units.append(outer["f58"])
        ref = outer["fe8"].FieldsValue
        assert (ref["f60"], ref["f64"], ref["fe8"], ref["f70"]) == (1, 0, 0, 0)
        assert (ref["f28"], ref["f30"], ref["f40"], ref["nf0"], ref["nd0"]) == (1e100, 1e100, None, 0, 0)
        roles, map_values = expected[row["word"]]
        data = ref["f18"]
        assert tuple((pair["key"], pair["value"]) for pair in data["f10"]) == map_values
        assert (data["f20"], data["f38"], data["f40_0"], data["f40_1"]) == ([], 0, 0, 0)
        for inline, source in zip(ref["f10"], roles, strict=True):
            member = inline["f08"]
            if source is None:
                assert member is None
                continue
            fields = member.FieldsValue
            key_type = lookup[member.ClassValue.NameValue]
            keeper = fields["f10"]["f10"].FieldsValue
            native_feature = keeper["f10"]
            file_owners.append(keeper["f08"])
            representations.append(member)
            key = (key_type, native_feature["f00"], native_feature["f08"], 0, fields["f38"])
            if key_type == 40:
                key += (fields["f3c"],)
            assert key == kernel_keys[source]
    assert len({id(owner) for owner in units}) == len(rows)
    collected = tuple(member["object"] for member in readback.FieldsValue["f40"])
    if collected:
        assert {id(rep) for rep in representations} == {id(rep) for rep in collected}
        assert len({id(owner) for owner in file_owners}) == len(collected)
    else:
        assert len({id(rep) for rep in representations}) == len(representations)
        assert len({id(owner) for owner in file_owners}) == 1
    actual_file = file_owners[0].FieldsValue
    assert ReadFileText(actual_file["shared"]["h18"]) == str(path)
    assert actual_file["refcfg"] == {"f08": "Default", "f10": 0}
    assert len(rows) == 6 and len(representations) == 30
    return atom, len(rows), len(representations)


def main():
    cli = ArgumentParser()
    cli.add_argument("variant", type=int, choices=(1, 2))
    args = cli.parse_args()
    for codec in ("utf-8", "utf-16le", "utf-16be", "latin-1", "cp1252"):
        lookup(codec)
    classes = registry()
    accesses = []
    active = True

    def guard(event, arguments):
        if active and event in ("open", "subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect"):
            accesses.append(event)
            raise RuntimeError("face constructor performed runtime operation: " + event)

    addaudithook(guard)
    try:
        path, archive, allocation = authored_prism(args.variant, classes)
        fields = prism_face_constructor_fields(archive, allocation, special_id_map_present=False)
        graph = collector_body(fields)
        raw, expected_map = write_component_body(graph)
        stored = store_part_caches(archive.streams, (ConfigurationCache(0, True, False, True, graph, False),))
        complete = BuildSldprt(stored, FormatVersion=4)
        readback = SldprtArchive.from_bytes(complete)
        assert all(readback.require(name) == data for name, data in archive.streams.items())
        assert readback.require(cache_path(0)) == raw
        decoded, found_map = read_component_body(raw)
        assert write_component_body(decoded)[0] == raw and found_map.CounterValue == expected_map.CounterValue
        atom, rows, reps = check_graph(decoded, archive, path)
        refused = 0
        for request in ((allocation, True), (replace(allocation, next_id=allocation.next_id + 1), False)):
            try:
                prism_face_constructor_fields(archive, request[0], special_id_map_present=request[1])
            except ValueError:
                refused += 1
            else:
                raise AssertionError("face constructor accepted a special map or inconsistent allocation")
    finally:
        active = False
    print(dumps({
        "passed": True, "scope": "ordinary mode-0 face constructor wrappers, before row validation",
        "variant": args.variant, "native_runs": 0, "runtime_io_attempts": len(accesses),
        "atom": atom, "rows": rows, "representations": reps, "refused": refused,
        "preserved_part_streams": len(archive.streams), "map_counter": found_map.CounterValue,
        "body_sha256": sha256(raw).hexdigest(), "part_sha256": sha256(complete).hexdigest(),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
