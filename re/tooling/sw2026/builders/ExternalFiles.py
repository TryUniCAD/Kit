from __future__ import annotations

from ntpath import basename, splitext

from Core import Obj
from builders.Metadata import integer


def file_definition(*, path_name: str, document_kind: str, created_at: int) -> dict:
    if not isinstance(path_name, str) or not path_name or "\x00" in path_name:
        raise ValueError("file references require an explicit nonempty path without null characters")
    types = {"part": (".sldprt", 2), "assembly": (".sldasm", 3), "drawing": (".slddrw", 4)}
    if not isinstance(document_kind, str) or document_kind not in types:
        raise ValueError("fresh file definitions support native part, assembly and drawing documents")
    if type(created_at) is not int or not 0 <= created_at <= 0xFFFFFFFF:
        raise ValueError("referenced document creation time must fit the archive timestamp field")
    name, extension = splitext(basename(path_name))
    required_extension, file_type = types[document_kind]
    if not name or extension.lower() != required_extension:
        raise ValueError("reference path extension must agree with its native document kind")
    return {
        "h18": Obj("moCStringHandle_c", {"f08": path_name}),
        "h10": Obj("moCStringHandle_c", {"f08": name}),
        "f20": file_type,
        "f08": 0,
        "f28": created_at,
        "f38": "",
        "f40": "",
        "f50": "",
        "f35": 0,
    }


def referenced_configuration(*, name: str | None, local_id: int | None) -> dict:
    if name is None and local_id is None:
        return {"f08": "", "f10": -1}
    if not isinstance(name, str) or not name or "\x00" in name:
        raise ValueError("referenced configuration names must be explicit nonempty strings")
    if type(local_id) is not int or not 0 <= local_id < 0x7FFFFFFF:
        raise ValueError("referenced configuration ids must identify an actual generated configuration")
    return {"f08": name, "f10": local_id}


def ordinary_self_reference(*, model, model_header, configuration, path_name, saved_at):
    kinds = {"moPart_c": ("part", "moPartConfiguration_c"), "moAssembly_c": ("assembly", "moConfiguration_c"),
             "moDrawing_c": ("drawing", None)}
    if not isinstance(model, Obj) or model.cls not in kinds:
        raise ValueError("self reference requires a generated model")
    kind, configuration_kind = kinds[model.cls]
    if configuration_kind is None:
        if configuration is not None:
            raise ValueError("drawing self-reference does not carry an active configuration")
        selected = referenced_configuration(name=None, local_id=None)
    elif not isinstance(configuration, Obj) or configuration.cls != configuration_kind or configuration["owner"] is not model:
        raise ValueError("self reference requires the model's actual active configuration")
    else:
        selected = referenced_configuration(name=configuration["f18"]["f08"], local_id=configuration["f08"])
    if not isinstance(model_header, Obj) or model_header.cls != "moHeader_c" or not model_header["fec"]:
        raise ValueError("self reference requires the generated model header")
    saved_at = integer(saved_at, "self reference save event", low=model_header["f50"])
    definition = file_definition(path_name=path_name, document_kind=kind, created_at=model_header["f70"])
    definition["h10"]["f08"] = model["f18"]["f08"]
    return Obj("moExtObject_c", {
        "shared": definition,
        "f58": 0,
        "f60": saved_at,
        "f48": 1,
        "f4c": 0,
        "f78": -1,
        "refcfg": selected,
        "f54": 0,
        "f70": 0,
        "f50": 0,
    })
