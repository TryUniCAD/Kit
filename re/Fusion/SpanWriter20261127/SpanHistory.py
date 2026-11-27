from dataclasses import replace

from convert.Formats.Fusion.BrepCodec.Topology.HistoryRecords import BuildHistory
from convert.Formats.Fusion.BrepCodec.History.EmitJournal import EmitJournal
from convert.Formats.Fusion.BrepCodec.Wire.CheckBrepRefs import CheckBrepRefs
from convert.Formats.Fusion.BrepCodec.Wire.EmitBrepHeader import EmitBrepHeader
from convert.Formats.Fusion.BrepCodec.Wire.EmitBrepRows import EmitBrepRows
from convert.Formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef


def emit_span_history(model,identity,tags,history,stamp):
    if model.BasePoint[2]==0 or model.BasePoint[2]+model.Height==0:
        raise ValueError('coincident sketch and end stations require a separately qualified source-link rule')
    records=BuildHistory(model,identity,tags)
    removed={index for index,record in enumerate(records) if record.NameValue=='ATTRIB_CUSTOM-attrib' and any(isinstance(value,CountedText) and value.Value=='sketch_attrib_def' for value in record.Fields)}
    assert len(removed)==2
    mapping={old:new for new,old in enumerate(index for index in range(len(records)) if index not in removed)}
    emitted=tuple(replace(record,Fields=tuple(EntityRef(mapping.get(value.Index,-1)) if isinstance(value,EntityRef) and value.Index>=0 else value for value in record.Fields)) for index,record in enumerate(records) if index not in removed)
    CheckBrepRefs(emitted,2)
    return EmitBrepHeader(stamp,2,True,50.0)+EmitBrepRows(emitted)+EmitJournal(history,len(emitted))
