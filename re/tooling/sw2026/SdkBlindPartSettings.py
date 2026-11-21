from __future__ import annotations

from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Header.HeaderInput import HeaderInput
from convert.adapters.solidworks.Archive.Construction.Metadata.HistoryInput import HistoryInput
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import FeatureTarget
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import PartBuildInput
from convert.adapters.solidworks.Archive.Construction.Presentation.StyleInput import StyleInput
from convert.adapters.solidworks.Archive.Construction.System.SystemInput import SystemInput
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import ModelDefInput


def settings(values):
    styles = values["styles"]
    style = StyleInput(styles["standard"], styles["font_name"], styles["line_style_name"], styles["language_id"],
                       tuple(styles["print_widths_m"]), tuple(styles["exclusion_names"]), tuple(styles["task_labels"]), tuple(styles["cutlist_expressions"]))
    unit = values["document_units"]
    analysis = values["analysis_units"]
    system = values["system"]
    provenance = values["provenance"]
    definition = values["definition"]
    return PartBuildInput(style, UnitInput(unit["length_unit"], unit["angle_unit"], unit["unit_system"], unit["decimal_places"]),
        UnitInput(analysis["length_unit"], analysis["angle_unit"], analysis["unit_system"], analysis["decimal_places"]),
        SystemInput(tuple(tuple(row) for row in system["folders"]), tuple(system["planes"].items()), system["cabinet_name"], system["origin_name"], system["origin_axis"], system["created_at"], system["construction_flag"]),
        FeatureTarget(values["target"]["date_code"], values["target"]["parasolid_version"]),
        HeaderInput(provenance["author"], provenance["company"], provenance["comment"], provenance["created_at"], provenance["modified_at"], provenance["updated_at"]),
        HistoryInput(provenance["created_at"], provenance["comment"], provenance["originating_build_code"], provenance["license_origin"], styles["language_id"], provenance["cjk_saved"]),
        ModelDefInput(definition["drafting_standard"], tuple(definition["detail_flags"]), tuple(definition["tessellation"]), definition["system_preference_7a"], definition["journal_name"], 19000),
        SelfFileInput(values["output"]["path_name"], values["output"]["saved_at"]), values["hatch_name"], values["manager_name"], values["density_kg_m3"], values["design_intent"], values["selected_leader"])
