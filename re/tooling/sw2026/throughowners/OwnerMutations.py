from copy import deepcopy
from dataclasses import replace


def mutate(document, probe):
    if probe is None:
        return document
    operations = tuple(value for value in document.feature_timeline if value.kind == "extrusion")
    stock, cut = operations
    sketches = {value.id:value for value in document.sketches}
    circle = sketches[cut.sketch_id]
    if probe in ("missing_center","extra_center","independent_center","fixed_circle"):
        arcs = tuple(value for value in circle.entities if value.kind == "circle")
        point = next(value for value in circle.entities if value.kind == "point")
        if probe == "missing_center":
            changed = replace(circle, entities=arcs)
        elif probe == "extra_center":
            changed = replace(circle, entities=(*circle.entities,replace(point,id=point.id+"extra")))
        elif probe == "fixed_circle":
            changed = replace(circle, entities=tuple(replace(value,fixed=True) if value.kind=="circle" else value for value in circle.entities))
        else:
            center = point.geometry.point
            changed = replace(circle, entities=tuple(replace(value,geometry=replace(point.geometry,point=replace(center,x=center.x+1))) if value is point else value for value in circle.entities))
        return replace(document, sketches=tuple(changed if value.id==circle.id else value for value in document.sketches))
    if probe in ("missing_normal","stale_normal_target","extra_normal_query","foreign_scope","automatic_scope"):
        choices = list(document.selections)
        if probe == "missing_normal":
            choices = [value for value in choices if value.id != document.selections[0].id]
        elif probe in ("stale_normal_target","extra_normal_query"):
            value = choices[0]
            query = dict(value.query)
            query["native_target_id" if probe=="stale_normal_target" else "unrepresented_intent"] = -99
            choices[0] = replace(value, query=query)
        else:
            index = next(index for index,value in enumerate(choices) if value.id in cut.selection_ids)
            value = choices[index]
            choices[index] = replace(value,path=(replace(value.path[0],entity_id=cut.id),)) if probe=="foreign_scope" else replace(value,query={"mode":"automatic"})
        return replace(document,selections=tuple(choices))
    if probe in ("lost_stock_parent","lost_cut_profile","new_body_stock","reverse_stock","cut_distance","missing_scope","foreign_profile_datum"):
        target = stock if probe in ("lost_stock_parent","new_body_stock","reverse_stock") else cut
        if probe == "lost_stock_parent":
            target = replace(target,input_feature_ids=())
        elif probe == "lost_cut_profile":
            target = replace(target,input_feature_ids=(stock.id,))
        elif probe == "new_body_stock":
            target = replace(target,operation="new_body")
        elif probe == "reverse_stock":
            target = replace(target,definition=replace(target.definition,reversed=True))
        elif probe == "cut_distance":
            target = replace(target,definition=replace(target.definition,length=document.parameters[0].value))
        elif probe == "missing_scope":
            target = replace(target,selection_ids=())
        else:
            target = next(value for value in document.feature_timeline if value.sketch_id==circle.id and value.kind!="extrusion")
            target = replace(target,input_feature_ids=(stock.id,))
        return replace(document,feature_timeline=tuple(target if value.id==target.id else value for value in document.feature_timeline))
    if probe in ("missing_datum","moved_datum","stale_datum_name"):
        planes=list(document.support_planes)
        index=next(index for index,value in enumerate(planes) if value.id != circle.support_plane_id)
        if probe=="missing_datum":
            planes.pop(index)
        elif probe=="stale_datum_name":
            planes[index]=replace(planes[index],name=planes[index].name+" changed")
        else:
            plane=planes[index]
            planes[index]=replace(plane,transform=replace(plane.transform,origin=replace(plane.transform.origin,x=1.0)))
        return replace(document,support_planes=tuple(planes))
    if probe in ("stale_driver","extra_driver"):
        driver=document.parameters[0]
        values=(replace(driver,owner_id=cut.id),) if probe=="stale_driver" else (driver,replace(driver,id=driver.id+"extra",name="D2"))
        return replace(document,parameters=values)
    if probe in ("stripped_history","stale_light_name","stale_scope","stripped_tree"):
        if probe=="stripped_history":
            return replace(document,feature_timeline=tuple(value for value in document.feature_timeline if value.sketch_id is not None))
        if probe=="stale_light_name":
            return replace(document,feature_timeline=tuple(replace(value,name=value.name+" changed") if value.name=="Directional1" else value for value in document.feature_timeline))
        metadata=deepcopy(dict(document.metadata))
        semantics=metadata["solidworks.typed_resolved_semantics"]
        if probe=="stale_scope":
            semantics["cut_body_dependency"]["producer_feature_id"]=-99
        else:
            semantics["native_tree"].pop("retained_public_ids")
        return replace(document,metadata=metadata)
    raise ValueError("unknown source mutation")
