from AuditConcentricDisplayState import ctext
from AssemblyMateDescriptor import make_mate_descriptor
from Core import Obj
from D01RevisionIntent import ordered_occurrences
from ProjectD01Concentric import require
from Streams import StreamDoc, load_rooted, store_rooted

from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakePlacement import (
    MakePlacement,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.ReadRigidXform import (
    ReadRigidXform,
)
from convert.adapters.solidworks.Archive.Construction.Units.UnitVocabulary import (
    KMassCodes,
    KUnitDomains,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    FieldText,
    ReadNodeName,
    ReadRows,
    RequireNode,
    RequireRecord,
)
from convert.adapters.solidworks.Core.TypedResolved.Units.ReadPartUnitNodes import (
    ReadUnitNodes,
)

CONTENT_INDEX = "SwDocContentMgr/SwDocContentMgrInfo"
CONFIG_FLAGS = -0x7FFBFE80


def object_list(nodes=()):
    return {"n": len(nodes), "items": [{"o": node} for node in nodes]}


def native_path(own_file, kind):
    fields = RequireRecord(RequireNode(own_file, "moExtObject_c").FieldsValue["shared"])
    require(FieldInt(fields, "f20") == kind, "content index has a different file kind")
    return ctext(fields["h10"]), ctext(fields["h18"])


def selected_config(manager):
    fields = RequireNode(manager, "moConfigurationMgr_c").FieldsValue
    selected = RequireNode(fields["f360"], "moConfiguration_c")
    (only,) = ReadRows(RequireRecord(fields["f370"])["items"])
    require(
        selected is fields["f368"] is only["o"],
        "content index requires a single actual active configuration",
    )
    return selected


def config_options(state, *, root):
    fields = RequireNode(state, "moConfigObject_c").FieldsValue
    options = RequireNode(fields["f08"], "moConfig_c").FieldsValue
    allowed_visibility = (1, 2) if root else (1,)
    require(
        FieldInt(options, "f08") == 2
        and FieldInt(options, "f0c") in allowed_visibility
        and FieldInt(fields, "f190") == 0,
        "content index requires ordinary resolved visible components",
    )
    return fields, FieldInt(options, "f08")


def configured_refs(root, configuration):
    refs = ordered_occurrences(root) if "f68" in root.FieldsValue else ()
    by_id = {
        FieldInt(RequireNode(row, "moReference_c").FieldsValue, "f08"): row
        for row in refs
    }
    require(
        len(by_id) == len(refs) and all(identity > 0 for identity in by_id),
        "content index occurrence identities must be positive and unique",
    )
    primary, *components = (
        row["o"] for row in ReadRows(configuration.FieldsValue["fce8"])
    )
    main_fields, main_suppression = config_options(primary, root=True)
    require(
        main_fields["f10"] is None and main_fields["f28"] == {"f08": "", "f10": -1},
        "content index root configuration row owns no occurrence",
    )
    ordered = []
    for component in components:
        fields, suppression = config_options(component, root=False)
        context = RequireNode(fields["f10"], "moContextChainComponent_c").FieldsValue
        chain = RequireNode(context["f20"], "moReferenceChain_c").FieldsValue
        record = RequireNode(chain["f08"], "moExtFeatureList_c").FieldsValue
        (link,) = ReadRows(record["f08"])
        target = RequireNode(link["o"], "moExtFeature_c").FieldsValue
        identity = FieldInt(target, "f44")
        require(
            identity in by_id,
            "content index configuration has a foreign or repeated occurrence",
        )
        occurrence = by_id.pop(identity)
        live = RequireNode(occurrence.FieldsValue["f4f8"], "moExtFeature_c").FieldsValue
        require(
            live["f50"] is occurrence
            and FieldInt(live, "f44") == identity
            and target["f50"] is None
            and ctext(target["f38"]) == ctext(live["f38"]) == ReadNodeName(occurrence)
            and fields["f28"] == occurrence.FieldsValue["f3c0"],
            "content index configuration links disagree with the actual occurrence",
        )
        ordered.append((occurrence, suppression))
    require(not by_id, "content index configuration omitted an actual occurrence")
    return main_suppression, tuple(ordered)


def header_identity(root, headers):
    own = []
    for header in headers:
        fields = RequireNode(header, "moHeader_c").FieldsValue
        title, path = native_path(fields["f38"], 3)
        own.append(
            (title, path, *(FieldInt(fields, key) for key in ("f70", "f48", "f40")))
        )
    first, second = own
    require(
        first == second and ReadNodeName(root) == first[0] and first[2] <= first[3],
        "content index header time and locator owners disagree",
    )
    return first


def unit_selection(root):
    table = ReadUnitNodes(root)
    length = FieldInt(table["length"].FieldsValue, "fb0")
    system = FieldInt(table["unit_system"].FieldsValue, "fb0")
    mass = FieldInt(table["density"].FieldsValue, "fc4")
    require(
        length in KUnitDomains["length"]
        and system in KUnitDomains["unit_system"]
        and mass in KMassCodes.values(),
        "content index unit selection is outside the known unit table",
    )
    return length, system, mass


def index_pose(fields):
    matrix, origin = ReadRigidXform(fields)
    return MakePlacement(PlaneFrame(origin, matrix[:3], matrix[3:6], matrix[6:9]))


def node_fields(
    identity, title, path, chosen, suppression, pose, *, root, blank=False, mates=()
):
    return {
        "f08": identity,
        "f0c": 0 if root else -1,
        "f10": int(not root),
        "f14": 5 if root else 1,
        "f18": title,
        "f20": suppression,
        "f28": chosen,
        "f30": path,
        "f38": int(root and not blank),
        "f40": object_list(),
        "f48": pose,
        "f50": object_list(mates),
        "f58": 1,
        "f5c": 0,
        "f68": object_list(),
        "fb0": int(blank),
    }


def part_row(occurrence, suppression, config_name):
    fields = occurrence.FieldsValue
    title, path = native_path(fields["f3b0"], 2)
    target = RequireRecord(fields["f3c0"])
    chosen = FieldText(target, "f08")
    require(
        title
        and path
        and chosen
        and FieldInt(target, "f10") >= 0
        and FieldInt(fields, "has_f360") == 1,
        "content index part needs a named selected target and rigid pose",
    )
    values = node_fields(
        FieldInt(fields, "f08"),
        title,
        path,
        chosen,
        suppression,
        index_pose(RequireRecord(fields["f360"])),
        root=False,
    )
    state = Obj("moConfigSpecificInfo", {"f08": config_name, "f10": 1})
    return Obj("moBCPartNode_c", values | {"fb8": object_list((state,))})


def content_document(root, configuration, headers, mates):
    if not isinstance(mates, tuple):
        raise TypeError("content index requires one ordered live mate list")
    model = RequireNode(root, "moAssembly_c")
    configuration = RequireNode(configuration, "moConfiguration_c")
    identity = FieldInt(model.FieldsValue, "f08")
    config_id = FieldInt(configuration.FieldsValue, "f08")
    config_name = ReadNodeName(configuration)
    require(
        identity == config_id == 0 and config_name,
        "content index requires an ordinary assembly and named root configuration",
    )
    title, path, created, updated, stamp = header_identity(model, headers)
    root_suppression, ordered = configured_refs(model, configuration)
    length, system, mass = unit_selection(model)
    blank = not ordered
    require(not blank or not mates, "a blank assembly cannot own content index mates")
    descriptors = tuple(
        make_mate_descriptor(model, configuration, mate) for mate in mates
    )
    identities = tuple(row["f3c"] for row in descriptors)
    require(
        len(set(identities)) == len(identities)
        and all(identity > 0 for identity in identities),
        "content index mate identities must be positive and unique",
    )
    pose = MakePlacement(
        PlaneFrame((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    )
    root_row = Obj(
        "moBCNode_c",
        node_fields(
            identity,
            title,
            path,
            config_name,
            root_suppression,
            pose,
            root=True,
            blank=blank,
            mates=descriptors,
        ),
    )
    parts = tuple(
        part_row(occurrence, suppression, config_name)
        for occurrence, suppression in ordered
    )
    configured = Obj("moBCConfigObjMapInfo_c", {"f08": object_list((root_row, *parts))})
    config = Obj(
        "moBCConfigurationInfo_c",
        {
            "f08": config_name,
            "f10": "ACTIVE",
            "f18": 0,
            "f1c": 0,
            "f20": configured,
            "f2c": config_id,
            "f30": CONFIG_FLAGS,
            "f34": 0,
            "f38": 0,
        },
    )
    mode = Obj(
        "moBCModeInfo_c",
        {
            "f08": path,
            "f10": created,
            "f28": title,
            "f30": int(blank),
            "f38": object_list((config,)),
            "fb0": config_name,
            "fb8": Obj("su_CStringArray", object_list(), schema=0),
            "f18": updated,
            "nc0": 1,
            "fc0": [{"k": config_name, "v": ""}],
            "ff4": length,
            "ff8": system,
            "ffc": mass,
            "f20": stamp,
            **{
                name: 0
                for name in (
                    "n40",
                    "n50",
                    "n60",
                    "nd0",
                    "ne0",
                    "n70",
                    "n80",
                    "n90",
                    "na0",
                )
            },
            **{
                name: []
                for name in (
                    "f40",
                    "f50",
                    "f60",
                    "fd0",
                    "fe0",
                    "f70",
                    "f80",
                    "f90",
                    "fa0",
                )
            },
        },
    )
    return StreamDoc("rooted", {"base": 1}, [mode])


def read_content_index(payload, reg):
    doc, reader = load_rooted(payload, reg, 1, 19000)
    require(
        not doc.tail and len(doc.roots) == 1 and doc.roots[0].cls == "moBCModeInfo_c",
        "content index requires one complete mode root",
    )
    return doc, reader.count


def make_content_index(root, configuration, headers, mates, reg):
    doc = content_document(root, configuration, headers, mates)
    return store_rooted(doc, reg, 19000)
