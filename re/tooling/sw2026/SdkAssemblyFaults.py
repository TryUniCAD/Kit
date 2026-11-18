from dataclasses import replace

from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import PlaneFrame
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


FAULTS = ("one_occurrence", "three_occurrences", "duplicate_occurrence", "nonrigid_frame", "feature_name_collision", "same_parent_child_path", "wrong_parent_kind", "provenance_disagreement", "wrong_effective_standard", "wrong_style_language", "wrong_child_manager_header", "wrong_child_model_class", "wrong_child_config_alias", "wrong_file_handle", "singular_transform", "wrong_child_config_owner")


def fault_inputs(name, child, inputs, occurrences, mate):
    if name == "one_occurrence":
        occurrences = occurrences[:1]
    elif name == "three_occurrences":
        occurrences = (*occurrences, occurrences[0])
    elif name == "duplicate_occurrence":
        occurrences = (occurrences[0], replace(occurrences[1], NameValue=occurrences[0].NameValue))
    elif name == "nonrigid_frame":
        frame = replace(occurrences[0].FrameValue, AxisU=(2.0, 0.0, 0.0))
        occurrences = (replace(occurrences[0], FrameValue=frame), occurrences[1])
    elif name == "singular_transform":
        frame = replace(occurrences[0].FrameValue, NormalValue=(0.0, 0.0, 0.0))
        occurrences = (replace(occurrences[0], FrameValue=frame), occurrences[1])
    elif name == "feature_name_collision":
        mate = replace(mate, NameValue=inputs.SystemValue.OriginName)
    elif name == "same_parent_child_path":
        file_value = child.HeaderValue.FieldsValue["f38"]
        inputs = replace(inputs, OutputValue=SelfFileInput(file_value.FieldsValue["shared"]["h18"].FieldsValue["value"].TextValue, inputs.OutputValue.SavedAt))
    elif name == "wrong_parent_kind":
        inputs = replace(inputs, OutputValue=SelfFileInput(inputs.OutputValue.PathName[:-7] + ".SLDPRT", inputs.OutputValue.SavedAt))
    elif name == "provenance_disagreement":
        inputs = replace(inputs, HistoryValue=replace(inputs.HistoryValue, CreatedAt=inputs.HistoryValue.CreatedAt + 1))
    elif name == "wrong_effective_standard":
        inputs = replace(inputs, StyleValue=replace(inputs.StyleValue, StandardValue=2))
    elif name == "wrong_style_language":
        inputs = replace(inputs, HistoryValue=replace(inputs.HistoryValue, LanguageId=1031))
    elif name == "wrong_child_manager_header":
        child = replace(child, ManagerHeader=ArchiveNode(RuntimeClass("moHeader_c", 1), {"f60": 0}))
    elif name == "wrong_child_model_class":
        model = ArchiveNode(RuntimeClass("moAssembly_c", 1), dict(child.SystemValue.RootValue.FieldsValue))
        child = replace(child, SystemValue=replace(child.SystemValue, RootValue=model))
    elif name == "wrong_child_config_alias":
        child = replace(child, ConfigValue=replace(child.ConfigValue, RootValue=ArchiveNode(RuntimeClass("moPart_c", 1), {})))
    elif name == "wrong_file_handle":
        source = child.HeaderValue.FieldsValue["f38"]
        shared = dict(source.FieldsValue["shared"])
        shared["h10"] = ArchiveNode(RuntimeClass("moCStringHandle_c", 1), {"value": "untyped"})
        file_value = ArchiveNode(source.ClassValue, {**source.FieldsValue, "shared": shared})
        child = replace(child, HeaderValue=ArchiveNode(child.HeaderValue.ClassValue, {**child.HeaderValue.FieldsValue, "f38": file_value}))
    elif name == "wrong_child_config_owner":
        old_config = child.CurrentConfig
        config = ArchiveNode(old_config.ClassValue, {**old_config.FieldsValue, "owner": None})
        child = replace(child, SystemValue=replace(child.SystemValue, ConfigValues=(config,)))
    else:
        raise ValueError("unknown complete assembly negative")
    return child, inputs, occurrences, mate
