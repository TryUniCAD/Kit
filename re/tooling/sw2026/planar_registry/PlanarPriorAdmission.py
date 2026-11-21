from dataclasses import replace
from hashlib import sha256
from math import isfinite

from RectanglePresentation import differences, observe, require


PRIOR = {
    "A20HeldoutPlaneCoincidentDistance": (
        "cc3b4267b0353b4f8b7a855d456dfe04aaa725b9f59873462aa1399843cb75bd",
        "31121fe7780b2e60840a68bf6c4eb01362b275533879dae44333a1c5d36ab115",
        2, ("coincident", "distance"),
    ),
    "A21HeldoutPlaneParallelDistance": (
        "476e37c3de6358bd687120a485b036f04cd4d488300f1287b794f2151803dff0",
        "e4bb77277f3ce27cde3892311724d1faac71ceb998fc74f765a084f8b16a51ff",
        3, ("parallel", "distance"),
    ),
}


def scope(case):
    from OriginalPlanarNames import PLANES

    require(set(case) == {"name", "split", "placements", "fixed_occurrence", "mates"}
            and case["split"] == "heldout" and case["name"] in PRIOR,
            "only the previously evaluated original planar cohort can enter this comparison")
    parent_sha, child_sha, occurrences, groups = PRIOR[case["name"]]
    require(len(case["placements"]) == occurrences
            and type(case["fixed_occurrence"]) is int and 0 <= case["fixed_occurrence"] < occurrences
            and tuple(item["kind"] for item in case["mates"]) == groups,
            "the prior cohort is limited to its two ordinary aligned mate roles")
    for pose in case["placements"]:
        require(set(pose) == {"axis", "angle_deg", "translation_m"} and pose["axis"] in ("x", "y", "z")
                and len(pose["translation_m"]) == 3
                and all(type(item) in (int, float) and isfinite(item)
                        for item in (pose["angle_deg"], *pose["translation_m"])),
                "an unsupported prior authored placement owner is present")
    for row in case["mates"]:
        distance = row["kind"] == "distance"
        require(set(row) in ({"kind", "planes", "distance_m"}, {"name", "kind", "planes", "distance_m"})
                if distance else set(row) in ({"kind", "planes"}, {"name", "kind", "planes"}),
                "an unsupported prior authored mate field is present")
        require(len(row["planes"]) == 2 and all(type(index) is int and 0 <= index < occurrences
                    and datum in PLANES.values() for index, datum in row["planes"])
                and (not distance or type(row["distance_m"]) in (int, float)
                     and isfinite(row["distance_m"]) and row["distance_m"] > 0),
                "a prior mate has a different endpoint or driving-value contract")
    return parent_sha, child_sha


def source_intent(source_document, authored_case, source_child_raw):
    from OriginalPlanarNames import project
    from OriginalPlanarRecipe import COMMON_CHILD_M, EDIT_INCREMENT_M
    from PlanarMateEdit import predict_edit
    from SdkPlanarGroupPrediction import transform

    parent_sha, child_sha = scope(authored_case)
    require(source_document.source.sha256 == parent_sha
            and sha256(source_child_raw).hexdigest() == child_sha,
            "use the exact prior native source custody identities")
    names = project(source_document, authored_case, COMMON_CHILD_M)
    require(source_document.assembly.documents[0].document.source.sha256 == child_sha,
            "the source document resolved a different physical child")
    case = {**authored_case, "mates": [
        {**row, "name": name}
        for row, name in zip(authored_case["mates"], names["mate_names"], strict=True)
    ]}
    require(all("name" not in row or row["name"] == name
                for row, name in zip(authored_case["mates"], names["mate_names"], strict=True)),
            "the locked authored and actual source mate names differ")
    distance, = [row["distance_m"] for row in case["mates"] if row["kind"] == "distance"]
    document = portable(case, names)
    return document, {
        "schema": "kit.sw2026.prior-planar-source-admission.v1",
        "source_intent": names,
        "original_case": case,
        "edited_case": predict_edit(case, distance + EDIT_INCREMENT_M, transform),
        "source_display": observe(source_child_raw, names["child"]["sketch_name"]),
        "ordered_mate_count": len(case["mates"]),
        "source_hashes": {"parent": parent_sha, "child": child_sha},
        "native_acceptance": False, "new_heldout_credit": 0,
    }


def admit(source_document, authored_case, source_child_raw, generated_child_raw):
    _, evidence = source_intent(source_document, authored_case, source_child_raw)
    generated = observe(generated_child_raw, evidence["source_intent"]["child"]["sketch_name"])
    presentation = compare_rows(evidence["source_display"], generated)
    return {**evidence, "presentation": presentation, "presentation_gate_passed": presentation["matches"]}


def compare_pair(source, generated, sketch_name):
    source_display = observe(source, sketch_name)
    generated_display = observe(generated, sketch_name)
    return compare_rows(source_display, generated_display)


def compare_rows(source_display, generated_display):
    changes = differences(source_display, generated_display)
    return {
        "actual_source": source_display, "actual_generated": generated_display,
        "differences": changes, "matches": not changes,
    }


def require_default_system(names):
    from convert.adapters.solidworks.Archive.Construction.Assembly.System.AsmVocabulary import KAsmFolders
    from convert.adapters.solidworks.Core.Preparation.DefaultPartTree import DefaultPartTree

    part = DefaultPartTree("Front Plane", 0)
    system = {"planes": dict(part.PlaneNames), "cabinet_name": part.CabinetName, "origin_name": part.OriginName}
    part_folders = dict(part.FolderValues)
    assembly_folders = {**part_folders, "moLiveSectionFolder_c": "Live Section Planes"}
    assembly = names["assembly"]["system"]
    group = assembly["mate_group_name"]
    require(names["child"]["system"] == {**system, "folder_names": part_folders}
            and assembly == {**system, "folder_names": {key: assembly_folders[key] for key in KAsmFolders},
                             "mate_group_name": group},
            "the ordinary writer cannot preserve the source folder, cabinet, origin or plane presentation")


def portable(case, names):
    from interchange.assembly.AssemblyEnums import MateAlignment, MateEntityKind, MateKind
    from interchange.assembly.MateConstraint import MateConstraint
    from interchange.assembly.MateEntity import MateEntity
    from interchange.assembly.TransformMatrix import TransformMatrix
    from interchange.Enums.EnumValues import ParameterRole, ValueKind
    from interchange.Records.RecordParameter import Parameter, ParameterValue
    from MakeAssemblyBoundaryCase import make_case, principal
    from OriginalPlanarRecipe import COMMON_CHILD_M, dimensioned_child
    from SdkPlanarGroupPrediction import transform

    scope(case)
    count = len(case["placements"])
    require(names["schema"] == "kit.sw2026.original-planar-authored-names.v1"
            and len(names["occurrence_names"]) == count and len(names["mate_names"]) == 2
            and all("name" not in row or row["name"] == name
                    for row, name in zip(case["mates"], names["mate_names"], strict=True)),
            "the prior recipe does not match the complete ordinary group inventory")
    require_default_system(names)
    root = make_case(count)
    graph = root.assembly
    root_def, child_def = graph.definitions
    child_name = "CohortChild"
    require(names["child"]["sketch_name"] == "Sketch1" and names["child"]["boss_name"] == "Boss-Extrude1",
            "the prior recipe names a different measured child type")
    root_planes = tuple(replace(row, name=names["assembly"]["system"]["planes"][axis])
                        for axis, row in zip("xyz", principal("root"), strict=True))
    child_planes = tuple(replace(row, name=names["child"]["system"]["planes"][axis])
                         for axis, row in zip("xyz", principal("child"), strict=True))
    child = dimensioned_child(child_name, COMMON_CHILD_M, names["child"]["configuration_name"])
    child = replace(child, support_planes=child_planes,
                    sketches=(replace(child.sketches[0], support_plane_id=child_planes[2].id),))
    root_config = replace(root.configurations[0], name=names["assembly"]["configuration_name"])
    child_config, = child.configurations
    definitions = (
        replace(root_def, name=case["name"], configuration_name=root_config.name),
        replace(child_def, name=child_name, configuration_name=child_config.name,
                configuration_id=child_config.id, body_ids=tuple(body.id for body in child.bodies)),
    )
    occurrences = []
    for index, (row, pose, label) in enumerate(zip(graph.instances, case["placements"], names["occurrence_names"], strict=True)):
        matrix = transform(pose)
        columns = (
            matrix[0], matrix[3], matrix[6], matrix[9] * 1000,
            matrix[1], matrix[4], matrix[7], matrix[10] * 1000,
            matrix[2], matrix[5], matrix[8], matrix[11] * 1000, 0., 0., 0., 1.,
        )
        occurrences.append(replace(row, name=label, transform=TransformMatrix(columns),
                                   fixed=index == case["fixed_occurrence"],
                                   configuration_name=child_config.name, configuration_id=child_config.id))
    entities, mates, parameters = [], [], []
    planes_by_name = {plane.name: plane for plane in child_planes}
    for order, (row, label) in enumerate(zip(case["mates"], names["mate_names"], strict=True)):
        name = f"mate/{order}"
        ends = []
        for index, (slot, datum) in enumerate(row["planes"]):
            entity = MateEntity(f"{name}/end/{index}", root_def.id, (occurrences[slot].id,),
                                MateEntityKind.PLANE, source_entity_id=planes_by_name[datum].id)
            entities.append(entity)
            ends.append(entity.id)
        value, owned = None, ()
        if row["kind"] == "distance":
            value = ParameterValue(row["distance_m"] * 1000, ValueKind.KLength, "mm")
            parameter = Parameter(name + "/D1", "D1", value, ParameterRole.KDriving, owner_id=name)
            parameters.append(parameter)
            owned = (parameter.id,)
        mates.append(MateConstraint(name, label, MateKind(row["kind"]), root_def.id, tuple(ends),
                                    order, value, owned, MateAlignment.KAligned))
    group, = graph.mate_groups
    group = replace(group, name=names["assembly"]["system"]["mate_group_name"],
                    mate_ids=tuple(mate.id for mate in mates))
    graph = replace(graph, definitions=definitions, instances=tuple(occurrences),
                    documents=(replace(graph.documents[0], document=child),),
                    mate_entities=tuple(entities), mates=tuple(mates), mate_groups=(group,))
    result = replace(root, configurations=(root_config,), parameters=tuple(parameters),
                     support_planes=root_planes, assembly=graph, metadata={"name": case["name"]})
    result.assert_valid()
    return result
