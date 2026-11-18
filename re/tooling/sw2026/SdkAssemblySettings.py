from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import AssemblyInput
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyMateIn import AssemblyMateIn
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblySysIn import AssemblySysIn
from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import OccurrenceIn
from convert.adapters.solidworks.Archive.Construction.Dimensions.DistanceInput import DistanceInput
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Geometry.MakePlaneFrame import MakePlaneFrame
from convert.adapters.solidworks.Archive.Construction.Header.HeaderInput import HeaderInput
from convert.adapters.solidworks.Archive.Construction.Metadata.HistoryInput import HistoryInput
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import FeatureTarget
from convert.adapters.solidworks.Archive.Construction.Presentation.StyleInput import StyleInput
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import ModelDefSettings


def assembly_settings(values):
    styles = values["styles"]
    unit = values["units"]
    system = values["system"]
    provenance = values["provenance"]
    definition = values["definition"]
    return AssemblyInput(values["name"], values["configuration_name"], values["manager_name"],
        StyleInput(styles["standard"], styles["font_name"], styles["line_style_name"], styles["language_id"], tuple(styles["print_widths_m"]), tuple(styles["exclusion_names"]), tuple(styles["task_labels"]), tuple(styles["cutlist_expressions"])),
        UnitInput(unit["length_unit"], unit["angle_unit"], unit["unit_system"], unit["decimal_places"]),
        AssemblySysIn(tuple(tuple(row) for row in system["folders"]), tuple(system["planes"].items()), system["cabinet_name"], system["origin_name"], system["mate_group_name"], system["created_at"]),
        FeatureTarget(values["target"]["date_code"], values["target"]["parasolid_version"]),
        HeaderInput(provenance["author"], provenance["company"], provenance["comment"], provenance["created_at"], provenance["modified_at"], provenance["updated_at"]),
        HistoryInput(provenance["created_at"], provenance["comment"], provenance["originating_build_code"], provenance["license_origin"], styles["language_id"], provenance["cjk_saved"]),
        ModelDefSettings(definition["drafting_standard"], tuple(definition["detail_flags"]), tuple(definition["tessellation"]), definition["system_preference_7a"], definition["journal_name"], 19000),
        SelfFileInput(values["output"]["path_name"], values["output"]["saved_at"]), definition["save_as_part_preferences"])


def occurrence_settings(values):
    return tuple(OccurrenceIn(row["name"], MakePlaneFrame(tuple(row["origin"]), tuple(row["u"]), tuple(row["v"]))) for row in values)


def mate_settings(values):
    distance = DistanceInput(values["distance_m"], values["design_intent"], values["selected_leader"]) if values["kind"] == "distance" else None
    return AssemblyMateIn(values["kind"], values["name"], values["axis"], values["fixed_occurrence"], distance)
