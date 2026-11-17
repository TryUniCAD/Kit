from __future__ import annotations

from Core import ArchiveError, Load, Obj
from MapBridge import schema_value
from Streams import StreamDoc, load_rooted, store_rooted
from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps


def make_node(descriptor):
    return Obj(descriptor.NameValue, schema=schema_value(descriptor))


def include_usage(reg, usage, ar, admitted, diagnostic=None):
    report = {
        "codec": "sdk_ordinary_cmgr", "admitted": admitted,
        "diagnostic": diagnostic, "usage": GetBodyReport(usage),
    }
    current = getattr(reg, "_usage", None)
    if current is not None:
        current.include_shared(report, ar)


def load_cmgr(data, reg, version=None, *, archive=None, name=None):
    if name is not None and name != "Contents/CMgr":
        raise ArchiveError("configuration manager bridge received another stream name")
    usage = BodyUsage()
    effective = 19000 if not version else version
    try:
        graph = ReadCmgrMut(bytes(data), effective, UsageValue=usage, NodeMaker=make_node)
    except BodyUnsupported as error:
        doc, ar = load_rooted(data, reg, 1, version)
        include_usage(reg, usage, ar, False, str(error))
        return doc, ar
    except (TypeError, ValueError, KeyError) as error:
        raise ArchiveError(f"invalid SDK configuration manager: {error}") from error
    ar = Load(data, 1, reg, version, dict(graph.ContextValue))
    ar._maps = ArchiveMaps(graph.MapValue.CounterValue, graph.MapValue)
    ar._maps.BaseValue = 1
    ar.p = len(ar.b)
    include_usage(reg, usage, ar, True)
    return StreamDoc("rooted", {"base": 1}, [graph.RootValue]), ar


def store_cmgr(doc, reg, version=None):
    usage = BodyUsage()
    effective = 19000 if not version else version
    try:
        if doc.head.get("base") != 1 or len(doc.roots) != 1 or doc.tail:
            raise BodyUnsupported("SDK manager requires one root, map base one and no tail")
        encoded = WriteCmgrMut(doc.roots[0], effective, UsageValue=usage)
    except BodyUnsupported as error:
        encoded = store_rooted(doc, reg, version)
        include_usage(reg, usage, None, False, str(error))
        return encoded
    except (TypeError, ValueError, KeyError) as error:
        raise ArchiveError(f"invalid SDK configuration manager emission: {error}") from error
    include_usage(reg, usage, None, True)
    return encoded
