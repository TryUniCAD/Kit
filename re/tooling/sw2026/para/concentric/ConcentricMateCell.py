from AssemblyModelExchange import ordinary_feature
from ExchangeMateEndpoints import project_exchange_mate_endpoints
from ExchangeMessagePack import ExchangeMap
from ExchangePack import OrderedMap

from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt

CONCENTRIC = "moMateConcentric"


def endpoint_cell(endpoint):
    if type(endpoint) is not ExchangeMap:
        raise ValueError(
            "concentric exchange endpoint requires a projected native wrapper"
        )
    dummy = endpoint.field("dummy")
    if type(dummy) is not ExchangeMap:
        raise ValueError(
            "concentric exchange endpoint requires a projected selected face"
        )
    return OrderedMap(
        (("class", endpoint.field("class")), ("dummy", OrderedMap(dummy.pairs)))
    )


def concentric_mate_cell(root, mate, child, *, historical_keeper_locator=None):
    name, identity, stamp = ordinary_feature(mate, CONCENTRIC)
    fields = mate.FieldsValue
    alignment = FieldInt(fields, "f3b4")
    locked = FieldInt(fields, "f4b8")
    if alignment not in (1, 2) or locked not in (0, 1) or FieldInt(fields, "f35c") != 0:
        raise ValueError("concentric exchange requires an ordinary unsuppressed mate")
    endpoints = tuple(
        endpoint_cell(endpoint)
        for endpoint in project_exchange_mate_endpoints(
            root, mate, child, historical_keeper_locator=historical_keeper_locator
        )
    )
    if len(endpoints) != 2:
        raise ValueError("concentric exchange requires two ordered endpoints")
    return OrderedMap(
        (
            ("Aligment", alignment),
            ("LockRotate", locked),
            ("NumberEntities", len(endpoints)),
            *((f"Ref{index}", value) for index, value in enumerate(endpoints)),
            ("class", CONCENTRIC),
            ("description", name),
            ("hidden", False),
            ("id", identity),
            ("suppressed", False),
            ("updatestamp", stamp),
        )
    )
