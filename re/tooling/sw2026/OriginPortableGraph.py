from __future__ import annotations

from math import isfinite


def require(condition, message):
    if not condition:
        raise ValueError(message)


def scalar(value):
    require(type(value) in (int, float) and isfinite(value), "portable source scalar must be finite")
    return float(value)


class Graph:
    def __init__(self, groups):
        self.nodes = {}
        for group in groups:
            for row in group.get("nodes", ()):
                identity = row["identity"]
                require(identity["concrete_runtime_class"] is True, "portable source contains an unresolved runtime class")
                key = identity["observation_key"]
                require(key not in self.nodes or self.nodes[key] == row, "portable source observer aliases disagree")
                self.nodes[key] = row

    def node(self, value, kind=None):
        identity = value["$node"] if "$node" in value else value
        row = self.nodes[identity["observation_key"]]
        require(row["identity"] == identity, "portable source reference identity differs")
        if kind is not None:
            require(identity["class"] == kind and identity["schema"] == 1, "portable source reference has the wrong concrete class: " + kind)
        return row

    def fields(self, value, kind=None):
        return self.node(value, kind)["fields"]

    def members(self, kind):
        return [row for row in self.nodes.values() if row["identity"]["class"] == kind]

    def text(self, value):
        if type(value) is str:
            return value
        if type(value) is dict and "$cstring" in value:
            require(type(value["$cstring"]) is str, "portable source CString text is invalid")
            return value["$cstring"]
        fields = self.fields(value)
        values = [self.text(fields[key]) for key in ("value", "f08") if key in fields]
        require(values and len(set(values)) == 1, "portable source text aliases are absent or disagree")
        return values[0]

    def name(self, value):
        return self.text(self.fields(value)["f18"])

    def children(self, value):
        fields = self.fields(value)
        rows = fields["f60"]["list"]
        require(rows["n"] == len(rows["items"]), "portable source child count differs")
        return [self.node(row["o"]) for row in rows["items"]]

    def handle(self, value, kind):
        fields = self.fields(value, kind)
        require(fields["f1c"] == -1 and fields["f08"] == 0, "portable source dimension handle is not local")
        index = fields["idx"]
        require(type(index) is int and 0 <= index <= 30591, "portable source dimension index is malformed")
        return index if index < 30591 else fields["f18"]


def endpoint(fields, name):
    value = fields[name + "_s"]
    require(type(value) is int and 0 <= value <= 65535, "portable source endpoint index is malformed")
    return value if value < 65535 else fields[name]


def check_drive(fields):
    require(all(fields.get(name) is None for name in ("f48", "f60")) and fields.get("f90") == 2,
            "portable source dimension has a tolerance attachment or non-driving mode")
    require(all(fields.get(name) == 0 for name in ("f54", "f5c", "f68", "has_f78", "f94", "f98")),
            "portable source dimension has suppressed or extended drive state")


def file_origin(graph, value):
    fields = graph.fields(value, "moExtObject_c")
    shared = fields["shared"]
    return {"path": graph.text(shared["h18"]), "model_name": graph.text(shared["h10"]),
            "kind": shared["f20"], "created_at": shared["f28"], "saved_at": fields["f60"],
            "configuration_name": graph.text(fields["refcfg"]["f08"]), "configuration_id": fields["refcfg"]["f10"]}
