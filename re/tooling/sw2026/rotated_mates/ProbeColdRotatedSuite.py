from contextlib import chdir
from importlib import import_module
from json import dumps
from math import isclose
from ntpath import basename
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from MakeQueueRotated import make_bundle
from ProveColdRotatedRead import ROOT, SCOPE, source_only
from VerifyRotatedMates import FORMAT, bind, finger, refuse, require


def compile_bundle(bundle):
    from BuildHistoricalRotated import build
    from ProjectRotatedModel import author_model
    from convert.adapters.solidworks.Core.AssemblyPreparation.PlanAsmWrite import PlanAsmWrite

    output = bundle["assembly"]["output"]
    with source_only(()) as accesses:
        model = author_model(bundle)
        plan = PlanAsmWrite(model, output["path_name"], output["saved_at"])
        (parent, _), (child, _) = build(bundle, plan)
    require(not accesses, "construction read an input file")
    return parent, child


def stage_bundle(folder, bundle, members):
    folder.mkdir()
    paths = tuple(
        folder / basename(bundle[role]["output"]["path_name"]) for role in ("assembly", "child")
    )
    for path, raw in zip(paths, members, strict=True):
        with path.open("xb") as stream:
            stream.write(raw)
    return paths


def inspect_graph(document, bundle, paths, hashes, *, geometry):
    graph = document.assembly
    require(
        graph is not None and len(graph.documents) == 1 and len(graph.definitions) == 2,
        "the graph lost its one actual shared part",
    )
    (linked,) = graph.documents
    child = linked.document
    require(
        (document.source.sha256, child.source.sha256) == hashes
        and Path(child.source.path).resolve() == paths[1],
        "the selected part was not the staged linked file",
    )
    root = next(row for row in graph.definitions if row.id == graph.root_definition_id)
    leaf = next(row for row in graph.definitions if row.document_id == linked.id)
    (root_config,) = document.configurations
    (child_config,) = child.configurations
    require(
        root_config.active
        and root_config.name == root.configuration_name == bundle["assembly"]["configuration_name"]
        and child_config.active
        and child_config.name
        == leaf.configuration_name
        == bundle["child"]["document"]["configuration_name"],
        "the active parent or linked part configuration changed",
    )
    require(
        tuple(row.fixed for row in graph.instances) == (True, False)
        and all(
            row.definition_id == leaf.id and row.configuration_name == child_config.name
            for row in graph.instances
        ),
        "the two physical occurrences lost their fixed or part selection state",
    )
    for row, intent in zip(graph.instances, bundle["occurrences"], strict=True):
        matrix, place = row.attributes["typed_placement_m"], intent["placement"]
        require(
            row.name == intent["name"]
            and all(
                isclose(actual, expected, rel_tol=0, abs_tol=2e-16)
                for actual, expected in zip(
                    (*matrix[:3], *matrix[4:7], *matrix[12:15]),
                    (*place["u"], *place["v"], *place["origin"]),
                    strict=True,
                )
            ),
            "a rotated placement was changed",
        )

    (group,) = graph.mate_groups
    require(
        group.owner_definition_id == root.id
        and group.mate_ids == tuple(row.id for row in graph.mates),
        "the physical mate sequence lost its root group",
    )
    datums = {row.id: row.name for row in child.support_planes}
    endpoints = {row.id: row for row in graph.mate_entities}
    selected = set()
    for order, (row, intent) in enumerate(zip(graph.mates, bundle["mates"], strict=True)):
        require(
            (row.order, str(row.kind), row.name) == (order, intent["kind"], intent["name"]),
            "the ordered native mate classes or names changed",
        )
        for identity, match in zip(row.entity_ids, intent["endpoints"], strict=True):
            endpoint = endpoints[identity]
            require(
                endpoint.owner_definition_id == root.id
                and str(endpoint.kind) == "plane"
                and endpoint.instance_path == (graph.instances[match["occurrence"]].id,)
                and datums[endpoint.source_entity_id] == match["datum"],
                "a real datum pick lost its occurrence or owner",
            )
            selected.add(identity)
    require(
        len(selected) == 6 == len(graph.mate_entities) and selected == endpoints.keys(),
        "the ordered mates must use all six distinct endpoints",
    )
    (driver,) = document.parameters
    distance = graph.mates[1]
    require(
        driver.name == "D1"
        and driver.role.value == "driving"
        and driver.owner_id == distance.id
        and distance.parameter_ids == (driver.id,)
        and driver.value == distance.value
        and driver.value.unit == "mm"
        and driver.value.value == 1000 * bundle["mates"][1]["distance_m"]
        and driver.provenance.native_id == "20",
        "the actual mate distance driver was not bound",
    )

    require((child.brep is not None) is geometry, "the linked child geometry read mode changed")
    if geometry:
        spec = bundle["child"]["document"]
        corners = spec["vertices_m"]
        volume = (
            (corners[1][0] - corners[0][0])
            * (corners[3][1] - corners[0][1])
            * spec["depth_m"]
            * 1e9
        )
        (body,) = child.bodies
        shape = body.topology
        require(
            (shape.solid_count, shape.face_count, shape.edge_count, shape.vertex_count)
            == (1, 6, 12, 8)
            and isclose(shape.volume, volume, rel_tol=1e-12),
            "the actual linked child geometry changed",
        )
    status = document.metadata["solidworks.typed_mates_semantics"]
    require(
        status["status"] == "admitted"
        and status["scope"] == SCOPE
        and status["mate_count"] == 3
        and status["full_selected_mate_graph"] is True
        and status["public_writer_qualified"] is False,
        "the cold reader scope lost its explicit writer exclusion",
    )
    return driver.value.value


def check_public(bundle, paths, members):
    from convert import open_document, write_document
    from convert.adapters.base.ReadOptions import ReadOptions
    from convert.adapters.registry.RegistryErrors import NotFoundError
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
    from convert.api.ApiContext import KConvertEngine

    schema = ROOT / "src/convert/adapters/solidworks/Config/RootLayout.json"
    hashes = tuple(finger(raw)["sha256"] for raw in members)
    parent, child = paths
    with source_only(paths, (schema,)) as access:
        full = open_document(parent, source_format=FORMAT, strict=True)
    require(
        access[parent.name] == 1 and access[child.name] == 1,
        "the public path must open both actual linked files once",
    )
    distance = inspect_graph(full, bundle, paths, hashes, geometry=True)
    with source_only(paths, (schema,)) as access:
        design = open_document(parent, source_format=FORMAT, strict=True, include_brep=False)
    require(
        access[parent.name] == 1 and access[child.name] == 1,
        "a design-only public path must open both actual linked files once",
    )
    inspect_graph(design, bundle, paths, hashes, geometry=False)
    with (
        chdir(parent.parent),
        Path(parent.name).open("rb") as stream,
        source_only(paths, (schema,)) as access,
    ):
        relative = open_document(stream, source_format=FORMAT, strict=True, include_brep=False)
    require(
        relative.source.path == parent.name and access[child.name] == 1,
        "a public stream must resolve the actual relative linked part once",
    )
    inspect_graph(relative, bundle, paths, hashes, geometry=False)
    require(
        full.parameters == design.parameters
        and all(
            getattr(full.assembly, item) == getattr(design.assembly, item)
            for item in ("instances", "mates", "mate_entities", "mate_groups")
        ),
        "the design-only read changed the graph",
    )

    options = ReadOptions(
        strict=True, values={"resolve_components": False, "discover_companions": False}
    )
    with source_only((parent,)) as access:
        deferred = KConvertEngine.read(parent, format_id=FORMAT, options=options)
    graph = deferred.assembly
    require(
        access == {parent.name: 1}
        and len(graph.instances) == 2
        and not graph.documents
        and graph.mates == design.assembly.mates
        and graph.mate_groups == design.assembly.mate_groups
        and deferred.parameters == design.parameters
        and tuple((row.id, row.instance_path, row.source_entity_id) for row in graph.mate_entities)
        == tuple((row.id, row.instance_path, row.source_entity_id) for row in design.assembly.mate_entities)
        and any(row.format_id == "solidworks.mates" for row in deferred.brep_payloads)
        and deferred.metadata["solidworks.typed_mates_semantics"]["status"] == "deferred",
        "a deferred graph must retain assembly-owned references and raw payload without loading children",
    )
    target = parent.parent.parent / "unpublished" / parent.name
    require(
        not SldprtWriter().supports(full, target), "the cold read cannot qualify a public writer"
    )
    try:
        write_document(full, target, destination_format=FORMAT, allow_carrier=False)
    except NotFoundError as error:
        require("does not support" in str(error), f"unexpected writer refusal: {error}")
    else:
        raise ValueError("the unchanged read-only group became writable through the registry")
    require(not target.parent.exists(), "the unqualified target was touched")
    return distance


def check_contrast(bundle, main, folder):
    from convert import open_document
    from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    rows = bundle["mates"]
    contrast = {
        **bundle,
        "mates": (
            {
                **rows[0],
                "kind": "coincident",
                "endpoints": tuple({**row, "datum": "Right Plane"} for row in rows[0]["endpoints"]),
            },
            *rows[1:],
        ),
    }
    members = compile_bundle(contrast)
    require(
        members[0] != main[0] and members[1] == main[1],
        "the alternate physical group must share the same linked part",
    )
    archive = SldprtArchive.from_bytes(members[0])
    link = ReadNativeLink(archive, 0, AssemblyValue=True)
    mate_list = ReadMatesMut(archive.require("Contents/Config-0-MatesList"), link.ResolvedValue)
    require(
        tuple(row.ClassValue.NameValue for row in mate_list.RootsValue)
        == (
            "moMateCoincident",
            "moMateDistanceDim_c",
            "moMateCoincident",
        ),
        "the alternate archive does not contain its authored physical mate classes",
    )
    paths = stage_bundle(folder, contrast, members)
    schema = ROOT / "src/convert/adapters/solidworks/Config/RootLayout.json"
    with source_only(paths, (schema,)):
        refuse(
            lambda: open_document(paths[0], source_format=FORMAT, strict=True), "has no entities"
        )
    return "coincident-distance-coincident"


def main():
    bind(ROOT)
    import_module("convert")
    with source_only(()) as accesses:
        bundle = make_bundle()
    require(not accesses, "the independent recipe read an input file")
    members = compile_bundle(bundle)
    with TemporaryDirectory(prefix="KitRotatedSuite-") as directory:
        folder = Path(directory).resolve()
        paths = stage_bundle(folder / "QualifiedRead", bundle, members)
        distance = check_public(bundle, paths, members)
        contrast = check_contrast(bundle, members, folder / "DifferentGroup")
    print(
        dumps(
            {
                "strict_modes": 2,
                "relative_linked_reads": 1,
                "deferred_modes": 1,
                "matched_endpoints": 6,
                "driver_mm": distance,
                "public_writer_qualified": False,
                "refused_class_shape": contrast,
                "construction_data_reads": 0,
                "files": {
                    path.suffix: finger(raw) for path, raw in zip(paths, members, strict=True)
                },
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
