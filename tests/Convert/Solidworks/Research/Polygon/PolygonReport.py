from __future__ import annotations

# process isolation needs observed graph results without sharing child memory
KReport = """
Report = {
    'point_count': Sketch['npoints'], 'line_count': Sketch['nlines'],
    'point_references': all(PointRefs), 'line_references': all(LineRefs),
    'point_creation_next': Sketch['f140']['f08'],
    'line_creation_next': Sketch['f140']['f0c'], 'marker_next': Sketch['f130'],
    'parameter_names': [Parameter['f18']['f08'] for Parameter in Parameters],
    'parameter_ids': [Parameter['f08'] for Parameter in Parameters],
    'dimension_ids': [Dimension['f50'] for Dimension in Dimensions],
    'expected_first_dimension_id': FirstDimId,
    'next_persistent_id': Allocator.next_id,
    'from_offset_id': Graph.from_offset.dimension['f50'],
    'from_offset_name': Graph.from_offset.parameter['f18']['f08'],
    'constructed_dimensions': len(Graph.constructed_dimensions),
    'dimension_refcounts': [Dimension['refcount'] for Dimension in Dimensions],
    'distinct_displays': len({id(Display) for Display in Displays}),
    'distinct_handles': len({id(Handle) for Handle in Handles}),
    'distinct_parameters': len({id(Parameter) for Parameter in Parameters}),
    'edited_depth': Edited['f18']['f850'][0]['o']['ff0']['f28']['f58'],
    'reverse_depth': Edited['f20']['f850'][0]['o']['ff0']['f28']['f58'],
    'stream_bytes': {Name: len(Data) for Name, Data in Streams.items()},
    'container_bytes': len(Container), 'runtime_reads': AuditValue.DeniedReads,
    'module_read_count': len(AuditValue.ModuleReads),
    'vendor_loadable': False, 'application_usable': False,
}
"""
