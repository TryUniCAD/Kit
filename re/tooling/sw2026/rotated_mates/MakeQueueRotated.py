from ntpath import join


def make_bundle():
    from convert.adapters.solidworks.Core.AssemblyPreparation.Recipe.AsmSavePolicy import (
        KAsmSavePolicy,
    )
    from convert.adapters.solidworks.Core.Preparation.DefaultPartTree import DefaultPartTree
    from convert.adapters.solidworks.Core.Preparation.MakePartStyle import MakePartStyle

    parent, child = "QueueRotated", "QueueDatumPrism"
    width, height, depth = 0.03175, 0.027625, 0.0135
    distance, vertical = 0.052125, 0.01875
    u, v = (0.6, 0.8, 0.0), (-0.8, 0.6, 0.0)
    created, saved = 1792346400, 1792347000
    locator = r"C:\KitRotatedComplete"
    tree = DefaultPartTree("Front Plane", created)
    style = MakePartStyle()
    target = {"date_code": 2026306, "parasolid_version": 370108}
    styles = {
        "standard": style.StandardValue,
        "font_name": style.FontName,
        "line_style_name": style.LineStyleName,
        "language_id": style.LanguageId,
        "print_widths_m": style.PrintWidths,
        "exclusion_names": style.ExclusionNames,
        "task_labels": style.TaskLabels,
        "cutlist_expressions": style.CutlistExpressions,
    }
    definition = {
        "drafting_standard": "moISO_c",
        "detail_flags": (),
        "tessellation": (26, 4, 25, True),
        "system_preference_7a": False,
        "journal_name": "Journal",
    }
    presentation = {
        "styles": styles,
        "cjk_saved": False,
        "units": {
            "length_unit": "mm",
            "angle_unit": "degree",
            "unit_system": "mmgs",
            "decimal_places": 4,
        },
    }
    folders, planes = dict(tree.FolderValues), dict(tree.PlaneNames)

    def provenance(name, start, end):
        return {
            "author": "Kit complete suite",
            "company": "",
            "comment": name,
            "created_at": start,
            "modified_at": end,
            "originating_build_code": target["date_code"],
            "license_origin": 0,
        }

    def output(name, suffix):
        return {"path_name": join(locator, name + suffix), "saved_at": saved}

    assembly = {
        "name": parent,
        "configuration_name": "Located",
        "origin_name": tree.OriginName,
        "mate_group_name": "Mates",
        "provenance": provenance(parent, created, saved - 25),
        "target": target,
        "output": output(parent, ".SLDASM"),
        "presentation": {
            **presentation,
            "assembly_features": {
                "folder_names": {**folders, "moLiveSectionFolder_c": "Live Section Planes"},
                "plane_names": planes,
                "cabinet_name": tree.CabinetName,
            },
            "definition": {**definition, "save_as_part_preferences": dict(KAsmSavePolicy)},
        },
    }
    part = {
        "document": {
            "name": child,
            "configuration_name": "Blank",
            "origin_name": tree.OriginName,
            "density_kg_m3": 1000.0,
            "plane_axis": "z",
            "depth_m": depth,
            "extrusion_name": "Boss-Extrude1",
            "sketch_name": "Sketch1",
            "rectangle_dimensions": {
                "width_text_m": (0.0, -0.9 * height),
                "height_text_m": (0.8 * width, 0.0),
                "route_centerline": False,
            },
            "vertices_m": tuple(
                (x * width / 2, y * height / 2) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))
            ),
        },
        "provenance": provenance(child, created - 105, saved - 140),
        "target": target,
        "output": output(child, ".SLDPRT"),
        "presentation": {
            **presentation,
            **definition,
            "cabinet_name": tree.CabinetName,
            "folder_names": folders,
            "folder_order": tuple(folders),
            "plane_names": planes,
            "hatch_name": "ANSI31 (Iron BrickStone)",
            "design_intent": False,
            "selected_leader": 0,
        },
    }
    occurrences = tuple(
        {"name": f"{child}-{index}", "placement": {"origin": origin, "u": u, "v": v}}
        for index, origin in enumerate(
            ((0.0, 0.0, 0.0), (distance * v[0], distance * v[1], vertical)), start=1
        )
    )
    mates = tuple(
        {
            "kind": kind,
            "name": name,
            "alignment": "aligned",
            "created_at": created + event,
            "fixed_occurrence": 0,
            "endpoints": tuple({"occurrence": index, "datum": datum} for index in range(2)),
            **({"distance_m": distance} if kind == "distance" else {}),
        }
        for kind, name, datum, event in (
            ("parallel", "LevelReference", "Front Plane", 73),
            ("distance", "SlideTravel", "Top Plane", 121),
            ("coincident", "CentreReference", "Right Plane", 192),
        )
    )
    return {"assembly": assembly, "child": part, "occurrences": occurrences, "mates": mates}
