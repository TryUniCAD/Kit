from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import json

from convert import open_document
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ProjectThruSrc import ProjectThruSrc
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.RequireThruFull import RequireThruFull
from OwnerDto import canonical, encode, require
from OwnerMutations import mutate
from OwnerSourceWire import observe
from Shape import read_shape
from Predict import predict


def main(request):
    require(set(request) in ({"source","sha256","output_name"},{"source","sha256","output_name","probe"}), "source observation request has unsupported fields")
    source=Path(request["source"])
    raw=source.read_bytes()
    require(sha256(raw).hexdigest()==request["sha256"], "disclosed source hash changed before read")
    source_wire=observe(raw)
    document=open_document(source)
    document=mutate(document,request.get("probe"))
    before=canonical(json.loads(document.to_json()))
    metadata=canonical(json.loads(document.to_json())["metadata"])
    plan=ProjectThruSrc(document,request["output_name"])
    shape=read_shape(document)
    prediction=predict(shape)
    stock=plan.InputValue.ShapeValue.StockValue
    circle=plan.InputValue.ShapeValue.CircleValue
    require(stock.VerticesValue[0]==shape["stock"]["minimum"] and stock.VerticesValue[2]==shape["stock"]["maximum"] and stock.DepthValue==shape["depth"] and stock.AxisValue==shape["support_axis"] and circle.CenterValue==shape["tool"]["center"] and circle.RadiusValue==shape["tool"]["radius"], "source owner input differs from the separately frozen analytic source projection")
    require(plan.EnvelopeValue.DocumentValue is document, "source envelope does not retain the actual complete document")
    refused=[]
    for envelope in (plan.EnvelopeValue,replace(plan.EnvelopeValue,UnmappedPaths=())):
        try:
            RequireThruFull(envelope)
        except ValueError as error:
            refused.append(str(error))
        else:
            raise ValueError("incomplete source passed full construction admission")
    require(before==canonical(json.loads(document.to_json())) and metadata==canonical(json.loads(plan.EnvelopeValue.DocumentValue.to_json())["metadata"]), "source or original metadata was altered during projection")
    tree=document.metadata["solidworks.typed_resolved_semantics"]["native_tree"]
    ids=tuple(value.id for value in document.feature_timeline)
    require(len(ids)==len(set(ids))==28, "projection did not retain every actual source presentation owner")
    require(sha256(source.read_bytes()).hexdigest()==request["sha256"], "source hash changed during read-only projection")
    return {"source_wire_observation":source_wire,"source_prediction":prediction,"source_projection":shape,"passed":True,"phase":"source","source_sha256":request["sha256"],"complete_document_sha256":sha256(before).hexdigest(),"original_metadata_sha256":sha256(metadata).hexdigest(),"original_document_identity_retained":True,"original_metadata_unchanged":True,"history_count":len(ids),"all_history_ids":ids,"history_names":tuple(value.name for value in document.feature_timeline),"system_lights":tuple(value.name for value in document.feature_timeline if value.name=="Ambient" or value.name.startswith("Directional")),"native_tree_status":tree["status"],"configuration_helpers":len(tree["configuration_helpers"]),"unrepresented_fields":plan.EnvelopeValue.UnmappedPaths,"complete_gate_refused":True,"cleared_gate_refused":True,"complete_gate_reasons":refused,"input":encode(plan.InputValue),"full_writer_outputs":0,"source_equivalence":False,"native_acceptance":False,"held_out_accessed":False,"oracle_used":False}
