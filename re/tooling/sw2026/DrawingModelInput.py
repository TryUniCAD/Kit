from __future__ import annotations

from dataclasses import replace
from uuid import UUID

from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import FeatureTarget
from convert.adapters.solidworks.Archive.Construction.Presentation.StyleInput import StyleInput
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Drawing.Construction.Model.DrawBuild import DrawBuild
from convert.adapters.solidworks.Drawing.Construction.Model.DrawFolders import DrawFolders
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetInput import SheetInput
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetNames import SheetNames


def drawing_build(request, probe=None):
    sheet, names, folders = (request[key] for key in ("sheet", "sheet_names", "folder_names"))
    presentation, provenance, target = (request[key] for key in ("presentation", "provenance", "target"))
    styles, units = presentation["styles"], presentation["units"]
    build = DrawBuild(
        request["name"],
        SheetInput(sheet["name"], sheet["paper_size"], sheet["scale_numerator"], sheet["scale_denominator"],
                   sheet["length_unit"], sheet["custom_property_view"]),
        SheetNames(names["plane_name"], names["profile_name"], names["detail_name"]),
        DrawFolders(folders["annotations"], folders["binder"], folders["comments"], folders["blocks"],
                    folders["ink_markups"], folders["review_markups"]),
        StyleInput(styles["standard"], styles["font_name"], styles["line_style_name"], styles["language_id"],
                   tuple(styles["print_widths_m"]), tuple(styles["exclusion_names"]), tuple(styles["task_labels"]),
                   tuple(styles["cutlist_expressions"])),
        UnitInput(units["length_unit"], units["angle_unit"], units["unit_system"], units["decimal_places"]),
        FeatureTarget(target["date_code"], target["parasolid_version"]),
        provenance["created_at"], UUID(provenance["block_identity"]), presentation["auto_dim_text_link"],
    )
    if probe == "model_name":
        build = replace(build, NameValue="")
    elif probe == "folder_name":
        build = replace(build, FolderValue=replace(build.FolderValue, BinderName=""))
    elif probe == "folder_contract":
        build = replace(build, FolderValue=None)
    elif probe == "sheet_scale":
        build = replace(build, SheetValue=replace(build.SheetValue, NumeratorValue=0))
    elif probe == "sheet_format":
        build = replace(build, SheetValue=replace(build.SheetValue, PaperSize="other-paper"))
    elif probe == "sheet_unit":
        build = replace(build, SheetValue=replace(build.SheetValue, LengthUnit="in"))
    elif probe == "creation_time":
        build = replace(build, CreatedAt=-1)
    elif probe == "block_identity":
        build = replace(build, BlockValue=UUID(int=0))
    elif probe == "block_type":
        build = replace(build, BlockValue=str(build.BlockValue))
    elif probe == "dimension_link":
        build = replace(build, AutoLink=1)
    elif probe == "style_contract":
        build = replace(build, StyleValue=None)
    elif probe == "style_standard":
        build = replace(build, StyleValue=replace(build.StyleValue, StandardValue=0))
    elif probe == "style_tasks":
        build = replace(build, StyleValue=replace(build.StyleValue, TaskLabels=("one",)))
    elif probe == "style_font":
        build = replace(build, StyleValue=replace(build.StyleValue, FontName=""))
    elif probe == "unit_contract":
        build = replace(build, UnitValue=None)
    elif probe == "target_contract":
        build = replace(build, TargetValue=None)
    elif probe == "service_pack":
        build = replace(build, TargetValue=replace(build.TargetValue, ServicePack=4))
    elif probe == "build_contract":
        build = None
    elif probe is not None:
        raise ValueError("unknown drawing root qualification probe")
    return build
