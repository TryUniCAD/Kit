from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from pathlib import Path
from struct import pack, unpack_from
from subprocess import check_output
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert import open_document
from convert.Geometry.Parasolid import ParaStream
from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import ReadActiveNodes
from convert.adapters.solidworks.Archive.Partition.ReadHistMarks import ReadHistMarks
from convert.adapters.solidworks.Archive.Partition.ReadXmtHistory import ReadXmtHistory
from convert.adapters.solidworks.Archive.Partition.SchemaHeader import SchemaHeader
from convert.adapters.solidworks.Container.Format import KPartitionStream

SCHEMA = "SCH_3701250_37102_13006"
CURRENT_PROFILE = b" created by modeller version 3701250"
PREDECESSOR_IDS = {"ladder": 1028, "local": 436}
NATIVE = {
    "ladder": (
        "v2026/corpus/ladder/L1_boss.SLDPRT",
        "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6",
        "eb41fea16306a3bf99ae82839e2d0f5bdcc75773bb4a819267800ccb8fb5a827",
        "a4231abb168b1188174ced656f4f1f01a2b8f3bb8d07a81f88f7dc9c9526ac7f",
        (1, 6, 12, 8), (177, 178), (7, 3),
    ),
    "local": (
        "v2026/corpus/local-import-readback/ConcaveOwned.SLDPRT",
        "fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33",
        "47e7343bcb7cce96604318603a1230aec3849d466b615dd01380d77516d1dfd2",
        "7ace723819c14c47b46dfc4fa9d73eb62b03541f29ca3b014d108c2d753a0fe5",
        (1, 8, 18, 12), (3, 4), (3, 2),
    ),
}
CONTROLS = {
    "one_light": (
        "v2026/corpus/light-counts/OneLights.SLDPRT",
        "b2772eebfd9f11038f72c76fe3a6ace4b9cd45373425f75921be45174943edb7",
        "88de93180e79df6ad22bff44aca85dcb6646594932910460f2784594ae6ffd03",
        "75132a3e1cfd947c6425b4b5987c3f892c32895ea3c4abb50c09f610bcdf1428",
        (1, 8, 14, 10), "current kernel framing differs",
    ),
    "legacy": (
        "examples/.SLDPRT/example.SLDPRT",
        "d1bbca099ccac1330024619390df3c6b76320a6a6c281a5009578b2fb63e7408",
        "3f3e3efbfbee0f41bda187579547881126cbf48101f006eecd759f491fc87ac6",
        "59d5eef7feb40d7a2ce52e20e50e14ca8eedaa1a1671b33a13fdc43720311cb7",
        (1, 31, 65, 45), "kernel history transmit profile is unqualified",
    ),
}


def digest(data):
    return sha256(data).hexdigest()


def load_case(parameters):
    name, source_hash, active_hash, history_hash, expected_shape, *_ = parameters
    relative = Path("re/solidworks") / name
    data = (ROOT / relative).read_bytes()
    assert digest(data) == source_hash
    document = open_document(
        data, source_format="solidworks.sldprt", strict=True,
        include_brep=True, include_tessellation=False,
    )
    skin = document.brep
    assert len(document.bodies) == 1 and skin is not None
    assert not skin.validate(frozenset(body.id for body in document.bodies))
    shape = tuple(len(rows) for rows in (skin.bodies, skin.faces, skin.edges, skin.vertices))
    assert shape == expected_shape
    active, history = tuple(p for p in document.brep_payloads if p.source_stream == KPartitionStream)
    assert (active.kind, history.kind) == ("partition", "deltas")
    assert (digest(active.data), digest(history.data)) == (active_hash, history_hash)
    observed = {
        "path": relative.as_posix(),
        "source_sha256": source_hash,
        "strict_document_sha256": digest(document.to_json(indent=None).encode()),
        "topology": shape,
        "partition": {"bytes": len(active.data), "schema": active.schema, "sha256": active_hash},
        "deltas": {"bytes": len(history.data), "schema": history.schema, "sha256": history_hash},
    }
    return active.data, history.data, observed


def guard_runtime():
    lookup("ascii")
    attempts = []

    def deny(event, args):
        if event in {"open", "subprocess.Popen", "os.system", "os.exec", "os.posix_spawn",
                     "socket.connect", "ctypes.dlopen"}:
            attempts.append(event)
            raise PermissionError(f"unexpected partition inspection access {event}")

    sys.addaudithook(deny)
    return attempts


def change_ref(data, offset, original, replacement):
    assert unpack_from(">H", data, offset)[0] == original + 1
    return data[:offset] + pack(">H", replacement + 1) + data[offset + 2 :]


def refuse(history, nodes, expected):
    for read in (ReadHistMarks, ReadXmtHistory):
        try:
            read(history, nodes)
        except ValueError as error:
            assert str(error) == expected, str(error)
        else:
            raise AssertionError(f"{read.__name__} accepted {expected}")
    return {"diagnostic": expected, "bytes": len(history), "sha256": digest(history)}


def ladder_refusals(history, nodes):
    deletion = pack(">HH", 3, 12)
    assert history[144:148] == pack(">HH", 1, 1)
    owner, = (offset for offset in range(148, 148 + 148 * 4, 4)
              if history[offset : offset + 4] == deletion)
    assert nodes[1].Integer("body") == 2 and nodes[2].KindValue == 12
    return {
        "detached_predecessor": refuse(
            change_ref(history, 115, 178, 1), nodes,
            "native history is not the witnessed linear rollback profile",
        ),
        "wrong_selected_mark": refuse(
            change_ref(history, 104, 177, 178), nodes,
            "native world and history identities disagree",
        ),
        "deleted_owner_missing": refuse(
            history[:owner] + history[owner + 4 :], nodes,
            "selected native rollback does not own the active body",
        ),
        "truncated_terminator": refuse(history[:-1], nodes, "current kernel record is truncated"),
        "appended_bytes": refuse(history + b"\0", nodes, "current kernel terminator differs"),
    }


def author_initial():
    start = pack(">HI", 239, 0)
    tail = pack(">HH", 1, 1)
    world = pack(">H", 101) + SchemaHeader(KKernelShapes[101])
    world += pack(">11H", 2, *(1,) * 10)
    world += pack(">B2H3i3H", 1, 1, 1, 1, 1, 0, 1, 1, 1)
    root = pack(">HBHHi", 3, 255, 3, 4, 1)
    mark = pack(">HB5H4iBi", 4, 255, 4, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1)
    return (
        ParaStream(start + world + tail, SCHEMA, b": TRANSMIT FILE (partition)" + CURRENT_PROFILE),
        ParaStream(start + root + mark + tail, SCHEMA, b": TRANSMIT FILE (deltas)" + CURRENT_PROFILE),
    )


def observations(case):
    if case == "initial":
        attempts = guard_runtime()
        active, history = author_initial()
        nodes = ReadActiveNodes(active)
        assert len(nodes) == 1 and nodes[1].Integer("body") == 0
        marks = ReadHistMarks(history, nodes)
        assert marks == (1, 0) and ReadXmtHistory(history, nodes) is None
        assert not attempts
        return {"partition_sha256": digest(active), "deltas_sha256": digest(history),
                "marks": marks, "validator_return": None}
    if case in CONTROLS:
        active, history, observed = load_case(CONTROLS[case])
        attempts = guard_runtime()
        nodes = ReadActiveNodes(active) if case == "one_light" else {}
        observed["typed_refusal"] = refuse(history, nodes, CONTROLS[case][-1])
        assert not attempts
        return observed
    active, history, observed = load_case(NATIVE[case])
    attempts = guard_runtime()
    nodes = ReadActiveNodes(active)
    slots = tuple(unpack_from(">H", history, offset)[0] - 1 for offset in (104, 115))
    expected_slots, expected_marks = NATIVE[case][-2:]
    assert slots == expected_slots
    assert unpack_from(">H", history, 113)[0] == slots[0] + 1
    prior_offset = PREDECESSOR_IDS[case]
    assert unpack_from(">H", history, prior_offset - 27)[0] == slots[1] + 1
    id_offsets = (140, prior_offset)
    assert tuple(unpack_from(">i", history, offset)[0] for offset in id_offsets) == expected_marks
    marks = ReadHistMarks(history, nodes)
    assert marks == expected_marks and ReadXmtHistory(history, nodes) is None
    observed.update(marks=marks, id_offsets=id_offsets, transmit_slots=slots, validator_return=None)
    if case == "ladder":
        observed["refusals"] = ladder_refusals(history, nodes)
    assert not attempts
    return observed


def main():
    cases = (*NATIVE, *CONTROLS, "initial")
    parser = ArgumentParser(description="Measure current Parasolid rollback mark identities")
    parser.add_argument("case", choices=("measure", *cases))
    selected = parser.parse_args().case
    if selected != "measure":
        print(json.dumps(observations(selected), sort_keys=True))
        return
    outcomes = {
        case: json.loads(check_output((sys.executable, "-I", "-B", str(HERE), case), timeout=45))
        for case in cases
    }
    print(json.dumps({
        "cases": outcomes, "guarded_fresh_processes": len(cases), "runtime_external_accesses": 0,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
