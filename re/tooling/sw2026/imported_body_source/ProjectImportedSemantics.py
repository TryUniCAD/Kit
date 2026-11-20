from collections.abc import Mapping
from types import MappingProxyType

from BuildImportedLocalPart import ImportedPartSemantics
from LocalBodyKernel import require
from ProjectDisclosedImport import FORMAT, active_configuration, source_owners
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import PartTextInput
from interchange import CadDocument


TEXT_SCOPE = "custom_properties"
DERIVED_NAME_OWNERS = frozenset(("implicit_kernel_and_key", "local_storage_key"))
AUTHORED_NAME_OWNER = "authored_atom_and_kernel"


def read_bag(value):
    require(isinstance(value, Mapping) and all(
        type(key) is str and type(member) is str for key, member in value.items()
    ), "source property scope lacks a complete ordinary literal text bag")
    return MappingProxyType(dict(value))


def project_part_text(document: CadDocument) -> PartTextInput:
    require(type(document) is CadDocument and document.source.format_id == FORMAT,
            "literal source text requires a strict SOLIDWORKS part")
    config = active_configuration(document)
    proof = document.metadata.get("solidworks.part_text_properties")
    require(isinstance(proof, Mapping) and proof.get("status") == "complete"
            and proof.get("profile") == "compatible_literal_text"
            and proof.get("binary_configuration_values") == "non_authoritative_cache"
            and proof.get("archive_version") == 19000 and proof.get("advanced_property_owners") is False,
            "source part text owners have no complete compatible projection")
    config_ids = (config.attributes["native_configuration_id"],) if TEXT_SCOPE in config.attributes else ()
    require(proof.get("configuration_ids") == config_ids,
            "source configuration text does not belong to the selected owner")
    return PartTextInput(
        read_bag(document.metadata.get("document_summary", {})),
        read_bag(document.metadata.get(TEXT_SCOPE, {})),
        read_bag(config.attributes.get(TEXT_SCOPE, {})),
    )


def read_local_names(document, feature, body):
    proof = document.metadata.get("solidworks.native_body_names")
    require(isinstance(proof, Mapping) and proof.get("status") == "complete"
            and proof.get("profile") == "current_single_local_solid_names"
            and proof.get("complete_brep_binding") is True
            and proof.get("storage_key") == feature.name and proof.get("body_count") == 1
            and proof.get("last_modifying_feature_id") == feature.attributes["native_object_id"]
            and body.attributes.get("solidworks.native_body") == proof
            and document.brep is not None and len(document.brep.bodies) == 1,
            "source import label owners have no complete local binding")
    kernel_body, = document.brep.bodies
    require(kernel_body.design_body_id == body.id and kernel_body.attributes.get("solidworks.native_body") == proof
            and body.name.strip() and body.name.isprintable(),
            "source body name does not belong to the selected local solid")
    owner = proof.get("name_owner")
    if owner == AUTHORED_NAME_OWNER:
        return body.name, True
    require(type(owner) is str and owner in DERIVED_NAME_OWNERS and body.name == feature.name,
            "source derived local body name does not match its native feature key")
    return body.name, False


def project_import_semantics(document: CadDocument) -> ImportedPartSemantics:
    feature, config, body = source_owners(document)
    body_name, authored = read_local_names(document, feature, body)
    return ImportedPartSemantics(feature.name, body_name, authored, config.name, project_part_text(document))
