from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from OwnerDto import require


def observe(raw):
    link=ReadNativeLink(SldprtArchive.from_bytes(raw),0)
    rows=[]
    for node in link.ResolvedValue.RootsValue:
        if node.ClassValue.NameValue not in ("moProfileFeature_c","moExtrusion_c","moICE_c") or ReadNodeName(node)=="Origin":
            continue
        fields=node.FieldsValue
        parents=fields["f60"]["list"]["items"]
        row={"name":ReadNodeName(node),"class":node.ClassValue.NameValue,"native_id":fields["f08"],"native_parent_names":[ReadNodeName(value["o"]) for value in parents],"native_parent_ids":[value["o"].FieldsValue["f08"] for value in parents]}
        if "pd_f78" in fields:
            support=fields["pd_f78"]
            row.update(support_reference_class=support.ClassValue.NameValue,support_datum_native_id=support.FieldsValue["ff0"]["f00"])
            require(not parents and support.ClassValue.NameValue=="moCompRefPlane_c", "disclosed native profile parent rule differs")
        else:
            require(len(parents)==1 and parents[0]["o"].ClassValue.NameValue=="moProfileFeature_c", "disclosed native operation has another history parent")
            row["operation_code"]=fields["f810"]
        rows.append(row)
    require(len(rows)==4,"disclosed native wire has another profile or operation")
    return {"observation_only":True,"is_generation_input":False,"archive_version":19000,"rows":rows}
