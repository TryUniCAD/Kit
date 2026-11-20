from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from pathlib import Path
from subprocess import check_output, run
from traceback import walk_tb
import codecs
import json
import sys


HERE = Path(__file__).resolve()
REPO = HERE.parents[4]
BASE = "5b51280a4d9ddf03a35445650a8c5c4077e523a3"
SELECTED = "748cdbec3fe61d6801f3d606e64fe42ecba95e9a647897be3fe3790570a889f3"
ALL_BODIES = "f87568db0dfa361ea44c42def01063c8ed07ea57c8270098cf3c60995e3e3b22"
SOURCES = {"ThroughMultiStock03": SELECTED, "ThroughAllBodies02": ALL_BODIES}
MODES = ("selected", "world-order", "retired-atom", "cross-producer", "detached-world",
         "cross-carrier", "detached-face", "pointer-mirror", "unrestricted")
REFUSALS = {
    "retired-atom": "saved kernel body does not identify a surviving stock atom",
    "cross-producer": "saved kernel body tag or producer differs from its surviving atom",
    "detached-world": "saved stock cache has detached or alternate world bodies",
    "cross-carrier": "saved stock body does not match its decoded faces and carriers",
    "detached-face": "saved stock cache has unowned native faces or shell topology",
    "pointer-mirror": "saved stock cache has alternate tracking pointer lanes",
    "unrestricted": "two stock cut requires its actual selected scope",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def refusal(action, mode):
    try:
        action()
    except ValueError as error:
        require(str(error) == REFUSALS[mode], f"unexpected {mode} refusal: {error}")
        return {"refusal": str(error)}
    raise ValueError("altered body ownership unexpectedly qualified: " + mode)


def change(nodes, index, **fields):
    item = nodes[index]
    nodes[index] = replace(item, FieldsValue={**item.FieldsValue, **fields})


def scope_delta(payload, nodes, read_history, read_header):
    try:
        read_history(payload, nodes)
    except ValueError as error:
        frames = {frame.f_code.co_name: frame.f_locals for frame, _ in walk_tb(error.__traceback__)}
        require(str(error) == "current kernel framing differs" and "ReadRollbackMut" in frames,
                "the exact separate delta refusal changed")
        mark = frames["ReadXmtHistory"]["MarkValue"]
        frame = frames["ExpectBytes"]
        cursor, expected = frame["self"], frame["Expected"]
        local = cursor.OffsetValue - len(expected)
        return {"error": str(error), "pmark_index": mark.IndexValue, "pmark_id": mark.Integer("id"),
                "delta_key": mark.Integer("delta_key"), "decompressed_offset": read_header(payload).body_offset + local,
                "expected_words": [int.from_bytes(expected[:2], "big"), int.from_bytes(expected[2:], "big")],
                "observed_words": [int.from_bytes(cursor.DataValue[local + shift:local + shift + 2], "big") for shift in (0, 2)]}
    raise ValueError("the previously open history boundary was silently admitted")


def worker(mode):
    sys.path.insert(0, str(REPO / "src"))
    from convert.Geometry.Parasolid import DecodePartData, ParaHeaderData
    from convert.adapters.solidworks.Archive.Partition.ReadXmtHistory import ReadXmtHistory
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import ReadBodyAttrs
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.MapStockBrep import MapStockBrep
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadCacheBodies import ReadCacheBodies
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadCacheFaces import ReadCacheFaces
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadStockCache import ReadStockCache
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadStockData import ReadStockData

    for encoding in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be"):
        codecs.lookup(encoding)
    for dependency in ("interchange.brep.Curves.BrepCurves", "interchange.brep.Validation.BrepValidate"):
        import_module(dependency)
    attempts = []

    def protect(event, _):
        if (
            event in {"open", "os.listdir", "os.scandir", "os.system", "os.exec", "os.fork",
                      "os.posix_spawn", "os.startfile"}
            or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg."))
        ):
            attempts.append(event)
            raise PermissionError("stock cache attempted external access: " + event)

    sys.addaudithook(protect)
    payload = sys.stdin.buffer.read()
    expected = ALL_BODIES if mode == "unrestricted" else SELECTED
    require(sha256(payload).hexdigest() == expected, "worker received unexpected source bytes")
    archive = SldprtArchive.from_bytes(payload)
    if mode == "unrestricted":
        result = refusal(lambda: ReadStockCache(archive), mode)
    else:
        cache = ReadStockCache(archive)
        nodes_value, decoded = ReadStockData(archive, cache.StreamName)
        nodes = dict(nodes_value)
        first, last = cache.BodyValues
        if mode == "selected":
            parts = []
            for body, brep in zip(cache.BodyValues, cache.BrepValue.bodies, strict=True):
                faces = ReadCacheFaces(nodes, body.KernelValue)
                parts.append({"body_index": body.KernelValue.IndexValue, "atom_id": body.AtomId,
                              "producer_id": body.ProducerValue.FieldsValue["f08"], "name": body.NameValue,
                              "design_body_id": brep.design_body_id, "brep_body_id": brep.id,
                              "regions": list(brep.region_ids), "face_carriers": faces})
            require([(row["body_index"], row["atom_id"], row["producer_id"], row["name"], len(row["face_carriers"]))
                     for row in parts] == [(2, 102, 40, "MovingStock", 6), (6, 103, 47, "ThroughFeature", 8)],
                    "the actual two body identities differ")
            require(replace(cache.BrepValue, bodies=decoded.bodies) == decoded,
                    "grouping changed other decoded geometry")
            _, history = DecodePartData(archive.require(cache.StreamName), cache.StreamName)
            delta = scope_delta(history.data, nodes, ReadXmtHistory, ParaHeaderData)
            require((delta["pmark_index"], delta["pmark_id"], delta["decompressed_offset"],
                     delta["expected_words"], delta["observed_words"])
                    == (378, 21, 144, [1, 1], [98, 65280]), "separate delta boundary changed")
            result = {"stream": cache.StreamName, "bodies": parts, "retired_atom_id": 101,
                      "unchanged_geometry_except_body_grouping": True, "history_boundary": delta}
        elif mode == "world-order":
            first_id, last_id = first.KernelValue.IndexValue, last.KernelValue.IndexValue
            change(nodes, 1, body=last_id)
            change(nodes, last_id, previous=0, next=first_id)
            change(nodes, first_id, previous=last_id, next=0)
            groups = ReadCacheBodies(nodes, cache.LineageValue)
            require([v.AtomId for v in groups] == [102, 103]
                    and MapStockBrep(nodes, decoded, groups) == cache.BrepValue, "physical order changed semantic grouping")
            result = {"reversed_world_chain": [last_id, first_id], "same_brep_and_body_order": True}
        elif mode in ("retired-atom", "cross-producer"):
            attributes = ReadBodyAttrs(nodes, last.KernelValue)
            name, value = ("ATOM_ID_2001", 101) if mode == "retired-atom" else ("LAST_BODY_MODIFYING_FEATURE_ID", 40)
            change(nodes, attributes[name].Indexes("fields")[1], values=(value,))
            result = refusal(lambda: ReadCacheBodies(nodes, cache.LineageValue), mode)
        elif mode == "pointer-mirror":
            attribute = ReadBodyAttrs(nodes, last.KernelValue)["ATOM_ID_2001"]
            fields = attribute.Indexes("fields")
            change(nodes, attribute.IndexValue, fields=(fields[1], fields[1]))
            result = refusal(lambda: ReadCacheBodies(nodes, cache.LineageValue), mode)
        elif mode == "detached-world":
            change(nodes, first.KernelValue.IndexValue, next=0)
            result = refusal(lambda: ReadCacheBodies(nodes, cache.LineageValue), mode)
        elif mode == "cross-carrier":
            first_face, *remaining = decoded.faces
            foreign = next(face for face in remaining if face.surface_id != first_face.surface_id)
            crossed = replace(decoded, faces=(replace(first_face, surface_id=foreign.surface_id), *remaining))
            result = refusal(lambda: MapStockBrep(nodes, crossed, cache.BodyValues), mode)
        else:
            face = next(node for node in nodes.values() if node.KindValue == 14)
            new_id = max(nodes) + 1
            nodes[new_id] = replace(face, IndexValue=new_id)
            result = refusal(lambda: MapStockBrep(nodes, decoded, cache.BodyValues), mode)
    require(not attempts, "cache worker attempted external access")
    return {**result, "external_access_attempts": len(attempts)}


def source(path, expected):
    actual = path.resolve(strict=True)
    require(not path.is_symlink() and actual.parts[-2:] == ("DisclosedNative", "ThroughMultiStock.SLDPRT")
            and SOURCES.get(actual.parts[-3]) == expected, "pass the declared disclosed sources")
    data = actual.read_bytes()
    require(sha256(data).hexdigest() == expected, "disclosed native source hash changed")
    return data


def prove(scoped, unrestricted):
    blobs = {False: source(scoped, SELECTED), True: source(unrestricted, ALL_BODIES)}
    phases = {}
    for mode in MODES:
        proc = run((sys.executable, "-I", "-B", str(HERE), "--worker", mode),
                   input=blobs[mode == "unrestricted"], capture_output=True)
        require(proc.returncode == 0, proc.stderr.decode())
        phases[mode] = json.loads(proc.stdout)
    source(scoped, SELECTED)
    source(unrestricted, ALL_BODIES)
    cache_path = REPO / "src/convert/adapters/solidworks/Core/TypedResolved/Cuts/MultiStock/Cache"
    return {"schema": "kit.sw2026.saved-two-stock-cache.v1", "baseline_revision": BASE,
            "worktree_head": check_output(("git", "rev-parse", "HEAD"), cwd=REPO, text=True).strip(),
            "source_sha256": SOURCES, "tool_sha256": sha256(HERE.read_bytes()).hexdigest(),
            "reader_sha256": {str(path.relative_to(REPO)): sha256(path.read_bytes()).hexdigest()
                              for path in sorted(cache_path.glob("*.py"))},
            "distinct_host_processes": len(phases), "phases": phases, "native_processes_started": 0,
            "generated_native_files": 0, "heldout_read_count": 0, "public_projection_qualified": False}


def main():
    parser = ArgumentParser()
    parser.add_argument("--selected", type=Path)
    parser.add_argument("--unrestricted", type=Path)
    parser.add_argument("--worker", choices=MODES)
    args = parser.parse_args()
    if not args.worker and (args.selected is None or args.unrestricted is None):
        parser.error("provide both disclosed source paths")
    result = worker(args.worker) if args.worker else prove(args.selected, args.unrestricted)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
