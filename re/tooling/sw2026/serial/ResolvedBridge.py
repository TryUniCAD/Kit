from __future__ import annotations

from Core import ArchiveError, ArchiveMap, Load, Obj
from MapBridge import schema_value
from Streams import StreamDoc
from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut


MBSM = "moPartConfiguration_c.SerializeMBSMDataObjects"


def make_node(descriptor):
    return Obj(descriptor.NameValue, schema=schema_value(descriptor))


def include_usage(reg, usage, ar, admitted, diagnostic=None):
    report = {"codec": "sdk_ordinary_resolved", "admitted": admitted,
              "diagnostic": diagnostic, "usage": GetBodyReport(usage), "full_linked_graph": False}
    current = getattr(reg, "_usage", None)
    if current is not None:
        current.include_shared(report, ar)


def load_sdk_resolved(data, reg, version=None, *, archive=None, name=None, seed=None, context_loader, fallback):
    context = context_loader(archive, name, reg, version)
    usage = BodyUsage()
    effective = 19000 if not version else version
    try:
        if seed is None:
            raise BodyUnsupported("SDK resolved loading requires its complete configuration map")
        graph = ReadResolvedMut(bytes(data), effective, seed.state, context, UsageValue=usage, NodeMaker=make_node)
    except BodyUnsupported as error:
        doc, ar = fallback(data, reg, version, archive=archive, name=name, seed=seed, _context=context)
        include_usage(reg, usage, ar, False, str(error))
        return doc, ar
    except (TypeError, ValueError, KeyError) as error:
        raise ArchiveError(f"invalid SDK resolved graph: {error}") from error
    ar = Load(data, graph.MapBase, reg, version, dict(context), seed=seed)
    ar._maps = ArchiveMaps(graph.MapValue.CounterValue, graph.MapValue)
    ar._maps.BaseValue = graph.MapBase
    ar.p = len(ar.b)
    head = {"base": graph.MapBase, "n": len(graph.RootsValue), "context": context}
    if graph.ExtraFields is not None:
        head["mbsm"] = Obj(MBSM, graph.ExtraFields)
    include_usage(reg, usage, ar, True)
    return StreamDoc("resolved", head, list(graph.RootsValue)), ar


def store_sdk_resolved_state(doc, reg, version=None, *, seed=None, fallback):
    usage = BodyUsage()
    effective = 19000 if not version else version
    try:
        if seed is None or doc.tail or doc.head.get("base") != seed.count:
            raise BodyUnsupported("SDK resolved emission requires its exact configuration prefix and no tail")
        extra = doc.head.get("mbsm")
        if extra is not None and (not isinstance(extra, Obj) or extra.cls != MBSM):
            raise BodyUnsupported("SDK resolved inline mapping requires its typed direct record")
        encoded, graph = WriteResolMut(tuple(doc.roots), None if extra is None else extra.f,
                                       effective, seed.state, doc.head["context"], UsageValue=usage)
    except BodyUnsupported as error:
        encoded, state = fallback(doc, reg, version, seed=seed)
        include_usage(reg, usage, None, False, str(error))
        return encoded, state
    except (TypeError, ValueError, KeyError) as error:
        raise ArchiveError(f"invalid SDK resolved emission: {error}") from error
    include_usage(reg, usage, None, True)
    return encoded, ArchiveMap(snapshot=graph.MapValue)
