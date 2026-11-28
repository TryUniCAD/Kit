import math

from SdkPlanarGroupPrediction import transform


PART_FOLDERS = (
    "moCommentsFolder_c", "moFavoriteFolder_c", "moHistoryFolder_c",
    "moSelectionSetFolder_c", "moSensorFolder_c", "moDocsFolder_c",
    "moSurfaceBodyFolder_c", "moSolidBodyFolder_c", "moEnvFolder_c",
    "moInkMarkupFolder_c", "moEqnFolder_c", "moMaterialFolder_c",
)
ASSEMBLY_FOLDERS = (
    "moCommentsFolder_c", "moFavoriteFolder_c", "moHistoryFolder_c",
    "moSelectionSetFolder_c", "moSensorFolder_c", "moLiveSectionFolder_c",
    "moDocsFolder_c", "moEnvFolder_c", "moInkMarkupFolder_c", "moEqnFolder_c",
)
PLANES = {"x": "Right Plane", "y": "Top Plane", "z": "Front Plane"}
PRINCIPAL_BASES = {"x": ((0., 0., -1.), (0., 1., 0.), (1., 0., 0.)), "y": ((1., 0., 0.), (0., 0., -1.), (0., 1., 0.)), "z": ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.))}


def require(value, message):
    if not value:
        raise ValueError(message)


def close_values(actual, expected):
    return len(actual) == len(expected) and all(math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-10) for a, b in zip(actual, expected, strict=True))


def canonical(placement):
    values = transform(placement)
    return [values[0], values[3], values[6], values[9] * 1000,
            values[1], values[4], values[7], values[10] * 1000,
            values[2], values[5], values[8], values[11] * 1000,
            0., 0., 0., 1.]


def label(value):
    require(type(value) is str and value and "\0" not in value, "an authored semantic name is missing or invalid")
    return value


def unique_names(document, kind):
    matches = [row.name for row in document.feature_timeline if getattr(row.definition, "object_data", {}).get("native_class") == kind]
    require(len(matches) == 1, "the source must expose one complete ordinary semantic role: " + kind)
    return label(matches[0])


def system_names(document, assembly):
    kinds = ASSEMBLY_FOLDERS if assembly else PART_FOLDERS
    actual_planes = {row.name: row for row in document.support_planes}
    require(len(document.support_planes) == 3 and set(actual_planes) == set(PLANES.values()), "only the three measured principal datum names are admitted")
    for axis, name in PLANES.items():
        plane = actual_planes[name]
        frame = plane.transform
        vector = lambda point: (point.x, point.y, point.z)
        require(plane.attributes.get("principal") is True and plane.support_selection_id is None and plane.offset_parameter_id is None and close_values(vector(frame.origin), (0., 0., 0.)) and all(close_values(vector(value), expected) for value, expected in zip((frame.x_axis, frame.y_axis, frame.z_axis), PRINCIPAL_BASES[axis], strict=True)), "the source datum has an unqualified principal frame or support")
    value = {"folder_names": {kind: unique_names(document, kind) for kind in kinds},
             "planes": dict(PLANES), "cabinet_name": unique_names(document, "moDetailCabinet_c"),
             "origin_name": unique_names(document, "moOriginProfileFeature_c")}
    if assembly:
        value["mate_group_name"] = unique_names(document, "moMateGroup_c")
    return value


def configuration(document):
    require(len(document.configurations) == 1 and document.configurations[0].active and not document.configurations[0].suppressed_feature_ids and not document.configurations[0].overrides, "the source requires one actual complete unsuppressed active configuration")
    return label(document.configurations[0].name)


def child_contract(child, dimensions):
    require(str(child.units) == "mm" and child.assembly is None and len(child.sketches) == 1 and len(child.bodies) == 1 and not child.materials and not child.meshes, "the child must be the ordinary unassigned single-body millimetre rectangle part")
    sketch, = child.sketches
    bosses = [row for row in child.feature_timeline if str(row.kind) == "extrusion"]
    require(len(bosses) == 1 and sketch.name == "Sketch1" and bosses[0].name == "Boss-Extrude1" and not sketch.suppressed, "the child requires its measured real sketch and boss roles")
    boss = bosses[0]
    allowed = {*PART_FOLDERS, "moDetailCabinet_c", "moRefPlane_c", "moOriginProfileFeature_c", "moProfileFeature_c"}
    require(all(row is boss or getattr(row.definition, "object_data", {}).get("native_class") in allowed for row in child.feature_timeline), "the child has an unsupported additional feature role")
    require(sketch.support_plane_id == next(row.id for row in child.support_planes if row.name == "Front Plane"), "the common child sketch has an unsupported support")
    value = boss.definition
    require(str(value.end_condition) == "blind" and not value.reversed and not value.symmetric and value.direction is None and value.second_end_condition is None and value.second_length is None and value.draft_angle is None and value.offset is None and not value.up_to_reference and value.second_draft_angle is None and value.second_offset is None and not value.second_up_to_reference, "the common child has an unsupported end condition direction or draft")
    require(value.length.unit == "mm" and math.isclose(value.length.value * .001, dimensions[2], rel_tol=1e-12), "the source boss differs from the independently authored common child contract")
    vertices = []
    require(len(sketch.entities) == 4, "the common child must contain exactly four actual line entities")
    for row in sketch.entities:
        require(str(row.kind) == "line" and not row.construction, "the common child includes an unsupported sketch entity")
        vertices.append((row.geometry.start.x * .001, row.geometry.start.y * .001))
    expected = [(-dimensions[0] / 2, -dimensions[1] / 2), (dimensions[0] / 2, -dimensions[1] / 2), (dimensions[0] / 2, dimensions[1] / 2), (-dimensions[0] / 2, dimensions[1] / 2)]
    require(all(close_values(a, b) for a, b in zip(vertices, expected, strict=True)) and all(close_values((row.geometry.end.x * .001, row.geometry.end.y * .001), expected[(index + 1) % 4]) for index, row in enumerate(sketch.entities)), "the common child rectangle differs from the independent authored recipe")
    require(sketch.closed_profile_entity_ids == (tuple(row.id for row in sketch.entities),), "the child has an unsupported profile membership or order")
    constraints = [row for row in sketch.constraints if not row.attributes.get("inferred")]
    require(len(constraints) == 6 and [str(row.kind) for row in constraints[:4]] == ["horizontal", "vertical", "horizontal", "vertical"], "the source child must retain exactly four actual axis relations and two actual driving lengths")
    require(all([(ref.entity_id, ref.point) for ref in relation.references] == [(entity.id, "")] for relation, entity in zip(constraints[:4], sketch.entities, strict=True)), "an actual source axis relation references a different sketch entity")
    require([str(row.kind) for row in constraints[4:]] in (["distance_x", "distance_y"], ["distance", "distance"]), "the child has an unqualified driving dimension role")
    sketch_owners = {sketch.id, *(row.id for row in child.feature_timeline if row.sketch_id == sketch.id and row.name == sketch.name)}
    parameters = {("Sketch1" if row.owner_id in sketch_owners else boss.name if row.owner_id == boss.id else "", row.name): row for row in child.parameters}
    require(len(child.parameters) == len(parameters) == 3 and set(parameters) == {("Sketch1", "D1"), ("Sketch1", "D2"), (boss.name, "D1")}, "the child has missing or additional parameter owners")
    for key, length in zip((("Sketch1", "D1"), ("Sketch1", "D2"), (boss.name, "D1")), dimensions, strict=True):
        parameter = parameters[key]
        require(str(parameter.role) == "driving" and parameter.value.unit == "mm" and math.isclose(parameter.value.value * .001, length, rel_tol=1e-12), "the common child driving value differs from the authored contract")
    require({row.parameter_id for row in constraints[4:]} == {parameters["Sketch1", "D1"].id, parameters["Sketch1", "D2"].id}, "the source child driving relations do not own the actual sketch parameters")
    for index, relation in enumerate(constraints[4:]):
        identity = sketch.entities[index].id
        require(relation.parameter_id == parameters["Sketch1", "D" + str(index + 1)].id and [(ref.entity_id, ref.point) for ref in relation.references] in ([(identity, "")], [(identity, "start"), (identity, "end")]), "an actual child driving length selects different geometry or parameter")
    return {"configuration_name": configuration(child), "sketch_name": sketch.name, "boss_name": boss.name, "system": system_names(child, False)}


def project(document, case, dimensions):
    document.assert_valid()
    require(str(document.units) == "mm", "the source assembly must retain the measured millimetre neutral convention")
    assembly = document.assembly
    require(not document.parameters and not document.bodies and not document.materials and not document.meshes, "the source assembly has unqualified extra modeled state")
    require(assembly is not None and len(assembly.documents) == 1 and len(assembly.definitions) == 2 and len(assembly.instances) == len(case["placements"]) and len(assembly.mates) == len(case["mates"]) and len(assembly.mate_entities) == 2 * len(assembly.mates), "the source graph is not a complete ordinary direct shared-part group")
    report = document.metadata.get("solidworks.typed_mates_semantics", {})
    require(report.get("status") == "admitted" and report.get("full_selected_mate_graph") is True and report.get("typed_occurrence_and_child_datum_identity") is True, "the source mate graph lacks complete typed occurrence and child identity")
    linked, = assembly.documents
    child = linked.document
    definitions = {row.id: row for row in assembly.definitions}
    require(assembly.root_definition_id in definitions, "the source lost its actual root definition")
    occurrences = tuple(assembly.instances)
    child_ids = {row.definition_id for row in occurrences}
    require(len(child_ids) == 1 and str(definitions[next(iter(child_ids))].kind) == "part", "the source must share one actual external part definition")
    child_names = child_contract(child, dimensions)
    indices = {}
    for index, (row, placement) in enumerate(zip(occurrences, case["placements"], strict=True)):
        require(row.owner_definition_id == assembly.root_definition_id and row.order == index and not any((row.suppressed, row.hidden, row.flexible, row.exclude_from_bom, row.attributes.get("virtual"))) and row.fixed == (index == case["fixed_occurrence"]), "the source occurrence has unqualified ownership state order or anchor")
        require(row.configuration_name == child_names["configuration_name"] and close_values(row.transform.values, canonical(placement)), "the source occurrence placement differs from the independent authored recipe")
        require(row.id not in indices, "the source repeated an occurrence identity")
        indices[row.id] = index
    entities = {row.id: row for row in assembly.mate_entities}
    planes = {row.id: row.name for row in child.support_planes}
    require(len(entities) == 2 * len(assembly.mates), "the source aliases unrelated mate endpoint identities")
    used = []
    for mate, expected in zip(assembly.mates, case["mates"], strict=True):
        require(mate.owner_definition_id == assembly.root_definition_id and str(mate.kind) == expected["kind"] and str(mate.alignment) == "aligned" and not mate.suppressed and mate.driving and len(mate.entity_ids) == 2, "the source mate has an unqualified kind alignment or partial endpoint graph")
        if expected["kind"] == "distance":
            require(mate.value is not None and mate.value.unit == "mm" and math.isclose(mate.value.value * .001, expected["distance_m"], rel_tol=1e-12), "the actual source distance differs from its authored recipe")
        else:
            require(mate.value is None, "a nondimensional source mate has an unsupported driving value")
        actual = []
        for identity in mate.entity_ids:
            entity = entities[identity]
            require(entity.owner_definition_id == assembly.root_definition_id and str(entity.kind) == "plane" and len(entity.instance_path) == 1 and entity.instance_path[0] in indices and entity.source_entity_id in planes, "the source endpoint lost its actual direct occurrence or selected child principal datum")
            actual.append([indices[entity.instance_path[0]], planes[entity.source_entity_id]])
            used.append(identity)
        require(actual == expected["planes"], "the complete source mate order or actual endpoint selection differs from the recipe")
    require(len(set(used)) == len(entities) and len(used) == len(entities), "the source contains orphaned or shared endpoint records")
    result = {"schema": "kit.sw2026.original-planar-authored-names.v1", "assembly": {"configuration_name": configuration(document), "system": system_names(document, True)}, "child": child_names,
              "occurrence_names": [label(row.name) for row in occurrences], "mate_names": [label(row.name) for row in assembly.mates]}
    require(len(set(result["occurrence_names"] + result["mate_names"])) == len(occurrences) + len(assembly.mates), "the source authored component and mate names collide")
    return result
