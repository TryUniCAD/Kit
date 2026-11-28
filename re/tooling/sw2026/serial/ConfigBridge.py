from __future__ import annotations

from Core import ArchiveError, ArchiveMap, Load, Obj
from MapBridge import schema_value
from Streams import StreamDoc
from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Header.HeaderRefNodes import HeaderRefNodes
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps


def make_node(descriptor):
    return Obj(descriptor.NameValue, schema=schema_value(descriptor))


def include_usage(reg, usage, ar, admitted, diagnostic=None):
    report = {
        "codec": "sdk_ordinary_config", "admitted": admitted,
        "diagnostic": diagnostic, "usage": GetBodyReport(usage),
        "full_linked_graph": False,
    }
    current = getattr(reg, "_usage", None)
    if current is not None:
        current.include_shared(report, ar)


def load_sdk_config(data, reg, version=None, *, archive=None, name="Contents/Config-0", load_header, read_items, fallback):
    if archive is None:
        raise ArchiveError(f"{name} requires its owning archive")
    header, header_reader = load_header(archive, name, reg, version)
    usage = BodyUsage()
    effective = 19000 if not version else version
    try:
        graph = ReadConfigMut(bytes(data), effective, header, UsageValue=usage,
                              NodeMaker=make_node, ReadItems=read_items)
    except BodyUnsupported as error:
        doc, ar = fallback(data, reg, version, archive=archive, name=name,
                           _header_info=(header, header_reader))
        include_usage(reg, usage, ar, False, str(error))
        return doc, ar
    except (TypeError, ValueError, KeyError) as error:
        raise ArchiveError(f"invalid SDK configuration graph: {error}") from error
    context = {**graph.ContextValue, "header_objects": HeaderRefNodes(header, effective, read_items)}
    ar = Load(data, 1, reg, version, context)
    ar._maps = ArchiveMaps(graph.MapValue.CounterValue, graph.MapValue)
    ar._maps.BaseValue = graph.MapBase
    ar.p = len(ar.b)
    ar.model_header_source = (name + "-ModelHeader", header_reader)
    include_usage(reg, usage, ar, True)
    return StreamDoc(name, {"model_header": header}, [graph.RootValue]), ar


def store_sdk_config_state(doc, reg, version=None, *, read_items, fallback):
    usage = BodyUsage()
    effective = 19000 if not version else version
    try:
        if len(doc.roots) != 1 or doc.tail or "model_header" not in doc.head:
            raise BodyUnsupported("SDK configuration requires one root, its typed header and no tail")
        encoded, graph = WriteConfigMut(doc.roots[0], effective, doc.head["model_header"],
                                        UsageValue=usage, ReadItems=read_items)
    except BodyUnsupported as error:
        encoded, state = fallback(doc, reg, version)
        include_usage(reg, usage, None, False, str(error))
        return encoded, state
    except (TypeError, ValueError, KeyError) as error:
        raise ArchiveError(f"invalid SDK configuration emission: {error}") from error
    include_usage(reg, usage, None, True)
    return encoded, ArchiveMap(snapshot=graph.MapValue)
