from convert.adapters.solidworks.Archive.Construction.Patterns.Emission.EmitPatArchive import EmitPatArchive
from convert.adapters.solidworks.Archive.Construction.Patterns.Emission.MakePatKeys import MakePatKeys
from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.PatPartGraph import PatPartGraph

from MakeLocalPattern import make_pattern


def shared_graph(graph):
    return PatPartGraph(
        graph.seed._shared(), graph.axis, graph.plane, graph.plane_driver, graph.pattern,
        graph.pattern_drivers, graph.headers,
    )


def make_keywords(graph):
    return MakePatKeys(shared_graph(graph))


def emit_pattern(seed_intent, axis_name, plane_intent, annotation, pattern_intent):
    graph = make_pattern(seed_intent, axis_name, plane_intent, annotation, pattern_intent)
    streams, container = EmitPatArchive(shared_graph(graph))
    return graph, streams, container
