from contextlib import contextmanager
from dataclasses import replace
from importlib import import_module

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from SweepArchiveLayout import BODY, GUARD, LAYOUTS, SWEEP
from SweepSectionTransport import encode_section_nodes, wrap_section
from SweepModel import require


RESOLVED = import_module("convert.adapters.solidworks.Archive.Resolved.WriteResolMut")
BODY_CODEC = import_module("convert.adapters.solidworks.Archive.Bodies.WriteBodyMut")


@contextmanager
def sweep_replay(*, cold=False):
    base_context, base_schema = RESOLVED.MakeResolvedCtx, BODY_CODEC.WriteSchemaMut

    def context(*args):
        value = base_context(*args)
        require(value.VersionValue == 19000 and value.FlagsValue == {
            "model_compressed_stream": 1, "model_is_part": 1, "cmgr_f658": 0 if cold else 1,
        }, "sweep replay requires the measured ordinary 19000 part context")
        classes = {name: (1,) for name in LAYOUTS if not name.startswith("sweep.")}
        return replace(value, LayoutsValue=value.LayoutsValue | LAYOUTS, SchemasValue=value.SchemasValue | classes,
                       VirtualValue=value.VirtualValue | {
                           (SWEEP, key): value.VirtualValue["moICE_c", key] for key in (1000, 1016, 1208, 1216)
                       })

    def schema(frame, name):
        fields = frame.ScopeValue.FieldsValue
        if name == BODY:
            nodes = tuple(row if isinstance(row, XmtNode) else XmtNode(row.index, row.kind, row.fields)
                          for row in fields["nodes"])
            frame.WriterValue.OutputValue.extend(wrap_section(encode_section_nodes(nodes)))
        elif name == GUARD:
            data = fields["f820"]
            if any(data[key] for key in ("f234", "f258", "f278")):
                raise BodyUnsupported("unqualified thin, circular-profile or alternate twist sweep")
        elif name == "sweep.noTangency19000":
            if fields["f7c"] or fields["f80"]:
                raise BodyUnsupported("unqualified sweep tangency owners")
        else:
            base_schema(frame, name)

    RESOLVED.MakeResolvedCtx, BODY_CODEC.WriteSchemaMut = context, schema
    try:
        yield
    finally:
        RESOLVED.MakeResolvedCtx, BODY_CODEC.WriteSchemaMut = base_context, base_schema
