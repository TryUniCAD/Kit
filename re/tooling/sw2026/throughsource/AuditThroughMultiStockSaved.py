from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import sys


SOURCE_SHA256 = "748cdbec3fe61d6801f3d606e64fe42ecba95e9a647897be3fe3790570a889f3"
HELPER_SHA256 = "20ef27e93692b42035ca629d667900dfc17bf77ab4fdcf2a3f43882371f8474f"
SOURCE_SUFFIX = ("ThroughMultiStock03", "DisclosedNative", "ThroughMultiStock.SLDPRT")
SURFACE_REPS = ("moFromSktEntSurfIdRep_c", "moEndFaceSurfIdRep_c")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def refusal(action):
    try:
        action()
    except ValueError as error:
        return str(error)
    raise ValueError("the scoped SDK guard unexpectedly admitted the multistock source")


def refs(face):
    for row in face.FieldsValue["f10"]:
        rep = row["f08"]
        if rep is not None and rep.ClassValue.NameValue in SURFACE_REPS:
            yield rep, rep.FieldsValue["f10"]["f10"]


def audit(payload):
    from AuditThroughAllDisclosed import graph, node_ref, roundtrip
    from convert import open_document
    from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
    from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ReadSourceOps import ReadSourceOps
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckCutWrapper import CheckCutWrapper
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckSavedCutScope import CheckCutScope
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadManagedCutAtoms import ReadCutAtoms
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSavedCutBodies import ReadCutBodies
    from convert.adapters.solidworks.Core.TypedResolved.ReadDepthOwner import ReadDepthOwner
    from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude

    archive, link, nodes, names = graph(payload)
    require(len(names) == len(link.ResolvedValue.RootsValue), "resolved root names are ambiguous")
    for graph_report in (link.ConfigValue.ReportValue, link.ResolvedValue.ReportValue):
        require(graph_report["completed"] and not graph_report["missing_schemas"]
                and not graph_report["provisional_schemas"], "the file exceeds the complete typed grammar")

    roles = ("SteadyStock", "MovingStock", "ThroughFeature")
    steady, moving, cut = (names[name] for name in roles)
    fields = cut.FieldsValue
    root = link.ConfigValue.RootValue
    manager = root.FieldsValue["fd88"]
    atom_objects = tuple(row["o"] for row in manager["atoms"])
    require(ReadCutAtoms(link) == set(atom_objects) and len(atom_objects) == 3,
            "the three solid atoms must alias the linked configuration map")

    body_owners = []
    for slot, atom in enumerate(atom_objects):
        producers = [name for name in roles if names[name].FieldsValue["f528"]["items"][0]["o"] is atom]
        consumers = [name for name in roles if names[name].FieldsValue["has_f530"]
                     and names[name].FieldsValue["f530"]["items"][0]["o"] is atom]
        require(len(producers) == 1, "an actual manager body needs one producer")
        body_owners.append({"slot": slot, "archive": node_ref(atom), "atom_id": atom.FieldsValue["f140"],
                            "producer_fields": [atom.FieldsValue[key] for key in ("f12c", "f130")],
                            "f144": atom.FieldsValue["f144"], "producer": producers[0], "consumers": consumers})
    require([(row["atom_id"], row["producer"], row["consumers"]) for row in body_owners]
            == [(103, roles[2], []), (102, roles[1], []), (101, roles[0], [roles[2]])],
            "producer and consumer pointers differ from the measured source")
    require(fields["f544"] == fields["has_f548"] == fields["f548"]["n"] == 1
            and all("f558" not in names[name].FieldsValue for name in roles),
            "cut lost its scoped wrapper or acquired an unmeasured field")
    wrapper, = (item["o"] for item in fields["f548"]["items"])
    wf = wrapper.FieldsValue
    face, component = (wf[key] for key in ("ff0", "f58"))
    CheckCutWrapper(root, steady, cut, atom_objects[2].FieldsValue["f140"])
    require(component.FieldsValue["owner"] is root and component.FieldsValue["has_ext"] == 0,
            "selected wrapper does not belong to the actual self component")
    face_refs = tuple(refs(face))
    require(len(face_refs) == 5 and len(face.FieldsValue["f10"]) == face.FieldsValue["f08"] == 6,
            "the selected face carrier incidence is incomplete")
    source_ext = face_refs[0][1].FieldsValue["f08"]
    producer_id = steady.FieldsValue["f08"]
    require(all(ref.FieldsValue["f10"]["f00"] == producer_id and ref.FieldsValue["f08"] is source_ext
                for _, ref in face_refs), "selected face subrefs do not share the stock producer")
    steady_chooser = steady.FieldsValue["f4a8"]
    require(steady_chooser["f68"] is steady and fields["f4c0"]["f68"] is cut,
            "chooser records are detached from their actual operations")
    chooser_refs = tuple(ref for row in steady_chooser["f48"]["items"][0]["o"].FieldsValue["f08"]["items"]
                         for _, ref in refs(row["o"]))
    require(len(chooser_refs) == 10 and all(ref.FieldsValue["f08"] is source_ext for ref in chooser_refs),
            "the selected face reference and stock chooser lost their shared external object")

    operations = {}
    for name in roles:
        node = names[name]
        entry = node.FieldsValue
        parent, = (item["o"] for item in entry["f60"]["list"]["items"])
        support = parent.FieldsValue["pd_f78"].FieldsValue["ff0"]["f00"]
        require(nodes[support].ClassValue.NameValue == "moRefPlane_c", "sketch support is not the actual datum")
        end = entry["f818"].FieldsValue
        driver = None if end["f18"] is None else ReadDepthOwner(link, end["f18"]).DepthValue
        operations[name] = {"archive": node_ref(node), "f810": entry["f810"], "f544": entry["f544"],
                            "parent": node_ref(parent), "support": node_ref(nodes[support]),
                            "end_words": {key: end[key] for key in ("f08", "f0c", "f10", "f88", "f8c")},
                            "driver": None if driver is None else {"name": driver.name, "metres": driver.native_value,
                                                                     "owner": driver.TypedOwner},
                            "f498": entry["f498"]}
    require(tuple((view["f810"], view["f544"]) for view in operations.values()) == ((-1, 0), (0, 0), (1, 1)),
            "the native independent-boss and cut roles differ")

    document = open_document(payload, source_format="solidworks.sldprt", include_tessellation=False)
    diagnostic = document.metadata["solidworks.typed_resolved_semantics"]
    require(diagnostic["status"] == "unsupported" and len(document.bodies) == 1,
            "the normal reader's first multistock boundary changed")
    replay = roundtrip(archive, link)
    require(len(replay) == 6 and all(row["byte_identity"] for row in replay.values()),
            "the six linked archives did not round-trip exactly in memory")
    return {
        "input_sha256": SOURCE_SHA256, "input_bytes": len(payload), "linked_streams": replay,
        "config_root": node_ref(root), "atom_manager_f260": manager["f260"], "atoms": body_owners,
        "operations": operations, "through_scope": {"has_f548": fields["has_f548"], "count": fields["f548"]["n"]},
        "selected_wrapper": {"archive": node_ref(wrapper), "component": node_ref(component), "component_is_config_root": True,
                             **{key: wf[key] for key in ("f18", "f1c", "f108", "n110", "f110", "f100", "f104")}},
        "selected_face_carrier": {"archive": node_ref(face), "f10_slots": len(face.FieldsValue["f10"]),
                                  "shared_external_object": node_ref(source_ext), "steady_chooser_alias_count": len(chooser_refs),
                                  "subrefs": [{"class": rep.ClassValue.NameValue, "f38": rep.FieldsValue["f38"],
                                               "owner": ReadNodeName(nodes[ref.FieldsValue["f10"]["f00"]]),
                                               "owner_record": ref.FieldsValue["f10"]} for rep, ref in face_refs]},
        "current_gates": {"public_reader": diagnostic["diagnostic"],
                          "new_stock_as_boss": refusal(lambda: ReadExtrude(link, moving, nodes)),
                          "all_managed_atoms": refusal(lambda: ReadCutBodies(steady, cut, set(atom_objects))),
                          "saved_scope": refusal(lambda: CheckCutScope(root, steady, cut, 101)),
                          "cold_wrapper": refusal(lambda: CheckCutWrapper(root, steady, cut, 101, IsCold=True)),
                          "source_plan": refusal(lambda: ReadSourceOps(document))},
        "public_fallback": {"bodies": [{"id": item.id, "final_feature_id": item.final_feature_id} for item in document.bodies],
                            "feature_steps": [{"id": item.id, "name": item.name, "operation": item.operation,
                                               "inputs": item.input_feature_ids, "selections": item.selection_ids,
                                               "definition": type(item.definition).__name__}
                                              for item in document.feature_timeline if item.name in roles]},
        "generated_native_files": 0,
    }


def main():
    parser = ArgumentParser(description="Read only the checksum-bound disclosed multistock source")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--sdk-root", type=Path, default=Path(__file__).resolve().parents[4])
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    require(source.parts[-3:] == SOURCE_SUFFIX and not args.source.is_symlink(),
            "pass the disclosed packet 03 native original")
    payload = source.read_bytes()
    require(sha256(payload).hexdigest() == SOURCE_SHA256, "the disclosed native source checksum differs")
    helpers = args.sdk_root / "re/tooling/sw2026"
    require(sha256((helpers / "AuditThroughAllDisclosed.py").read_bytes()).hexdigest() == HELPER_SHA256,
            "the exact linked stream auditor changed")
    sys.path[:0] = [str(args.sdk_root / "src"), str(helpers)]
    print(json.dumps(audit(payload), sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
