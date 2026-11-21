from __future__ import annotations

import argparse
from functools import partial
from hashlib import sha256
from json import dumps, loads
from math import isfinite, sqrt
from pathlib import Path
from struct import pack
from uuid import NAMESPACE_URL, uuid5

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadFieldsMut import ReadFieldsMut
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadSchemaMut import ReadSchemaMut
from convert.adapters.solidworks.Archive.Definition.Fields.DefPrefixFields import KDefPrefixFields
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Drawing.Definition.Emission.ReadBlankKids import ReadBlankKids
from convert.adapters.solidworks.Drawing.Definition.Emission.ReadDrawMut import ReadDrawMut
from convert.adapters.solidworks.Drawing.Definition.Linked.BindFrontMut import BindFrontMut
from convert.adapters.solidworks.Drawing.Definition.Linked.FrontLayouts import KFrontLayouts
from convert.adapters.solidworks.Drawing.Definition.Linked.FrontSchemas import KFrontSchemas
from convert.adapters.solidworks.Drawing.Definition.Linked.FrontVirtuals import KFrontVirtuals
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import NeedConceptNode
from convert.adapters.solidworks.Drawing.Identity.DrawingIdentity import KDrawClsid


def digest(data):
    return sha256(data).hexdigest()


def require(condition, error):
    if not condition:
        raise ValueError(error)


def exact(path, identity):
    data = path.read_bytes()
    require(digest(data) == identity, f"disclosed source hash mismatch for {path.name}")
    return data


def raw_graph(data):
    context = BodyContext(19000, KFrontLayouts, KFrontVirtuals, KFrontSchemas)
    context.FlagsValue["owner_is_drawing"] = 1
    cursor = BinaryReader(data)
    reader = GraphReader(cursor, ArchiveMaps(1), partial(ReadDrawMut, context))
    doc = ArchiveNode(RuntimeClass("uiDrawingDoc_c", 1), {})
    frame = ReadFrame(context, reader, FieldScope(doc.FieldsValue), doc, ReadSchemaMut, ReadFieldsMut)
    ReadFieldsMut(frame, KDefPrefixFields)
    require(cursor.TakeBytes(len(KDrawClsid)) == KDrawClsid, "reading requires an actual drawing Definition")
    ReadBodyMut(context, reader, doc)
    require(cursor.GetRemaining() == 0, "drawing Definition did not consume all bytes")
    BindFrontMut(doc)
    return doc


def field(owner, selector, name):
    return NeedConceptNode(owner.FieldsValue[selector], name)


def sole(owner, selector, name):
    collection = owner.FieldsValue[selector]
    row, = collection["items"]
    require(collection["n"] == 1, "expected the ordinary single-member list")
    return NeedConceptNode(row["o"], name)


def xyz(owner, key):
    value = owner.FieldsValue[key]
    result = tuple(value[axis] for axis in "xyz")
    require(all(type(component) is float and isfinite(component) for component in result), "expected finite point coordinates")
    return result


def close(a, b, absolute=1e-15):
    return len(a) == len(b) and max(abs(l-r) for l,r in zip(a,b,strict=True)) <= absolute


def note_semantics(doc):
    model = field(doc, "model", "moDrawing_c")
    sheet = field(model, "f1430", "moDrSheet")
    require(sum(x is sheet for x in ReadBlankKids(model)) == 1, "active sheet is not owned by the drawing")
    children = ReadBlankKids(sheet)
    require(tuple(x.ClassValue.NameValue for x in children) ==
            ("moRefPlane_c","moProfileFeature_c","moDetailFolder_c"), "expected an unlinked sheet with its actual detail folder")
    folder = field(sheet, "f390", "moDetailFolder_c")
    require(children[-1] is folder, "sheet detail folder identity changed")
    display = sole(folder, "f358", "moDisplayNote_c")
    component = field(display, "f48", "moCompNote_c")
    note = field(component, "fe8", "moNoteData_c")
    text = field(note, "f98", "moGenericText_c")
    require(display.FieldsValue["f30"] is folder and note.FieldsValue["f48"] is folder and text.FieldsValue["f170"] is display,
            "display folder and text owner links must resolve to the actual nodes")
    require(component.FieldsValue["f58"] is None, "the selected note must lack a component attachment")
    absolute = sole(note, "f58", "moAbsolutePoint_c")
    attach_cache = sole(display, "f298", "moAttachPointData_c")
    require(attach_cache.FieldsValue["f38"] is None, "plain note must lack a linked attachment view")
    point, attach, vector = xyz(text,"f38"), xyz(display,"f290"), xyz(display,"f628")
    require(close(attach,xyz(absolute,"f08")) and close(attach,xyz(absolute,"f28"))
            and close(attach,xyz(attach_cache,"f08")) and close(attach,xyz(attach_cache,"f20")),
            "independent attachment point owners disagree")
    delta = tuple(a-b for a,b in zip(point,attach,strict=True))
    length = sqrt(sum(x*x for x in delta))
    require(length > 0, "the visual note and attachment must occupy distinct points")
    predicted_vector = tuple(x/length for x in delta)
    list_node = field(text,"f158","moGenTextDataList_c")
    array = field(list_node,"f10","suObArray")
    first,*tail = array.FieldsValue["items"]
    NeedConceptNode(first["o"],"moTextDataLineHead_c")
    codes = tuple(NeedConceptNode(row["o"],"moTextDataChar_c").FieldsValue["f40"] for row in tail)
    require(codes and all(type(value) is int and 0 <= value <= 65535 for value in codes), "selected text needs typed UTF-16 code units")
    from_chars = pack("<"+"H"*len(codes),*codes).decode("utf-16-le")
    raw_string = text.FieldsValue["f08"]
    require(raw_string == from_chars and from_chars and not any(x in from_chars for x in "\0\r\n"),
            "the independent stored text roles must agree on one plain line")
    return from_chars, point, {"note_persistent_id":note.FieldsValue["f08"],"character_code_units":len(codes),
                              "text_roles_agree":True,"point_differs_from_attachment":True,
                              "arrow_direction_matches_normalized_delta":close(vector,predicted_vector),
                              "inherits_default_character_format":text.FieldsValue["f18"] is None}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source-lock",type=Path,required=True)
    parser.add_argument("--source-lock-sha256",required=True)
    parser.add_argument("--disclosed-sources-directory",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    lock=loads(exact(args.source_lock,args.source_lock_sha256))
    require(lock["passed"] and lock["distinct_passing_processes"]==14,"plain-note authoring lock did not pass")
    records={name:case for name,case in lock["source_cases"].items() if case["private"] is False}
    require(set(records)=={"Disclosed01","Disclosed02"},"there must be exactly two disclosed plain-note sources")
    report={"schema":"kit.sw2026.disclosed-plain-note-projection.v1","source_lock_sha256":args.source_lock_sha256,
            "native_sessions_started":0,"heldout_files_read":0,"writer_output_count":0,"normal_drawing_admission":False,
            "locations_from_generic_text":True,"records":[]}
    for case,record in sorted(records.items()):
        root=args.disclosed_sources_directory/case
        intent=loads(exact(root/"Intent.json",record["intent_sha256"]))
        for stage,tail in (("original",""),("edited","Edit")):
            blob=exact(root/(case+tail+".SLDDRW"),record[stage+"_sha256"])
            definition=SldprtArchive.from_bytes(blob).require("Contents/Definition")
            text, point, metrics=note_semantics(raw_graph(definition))
            tag="initial" if stage=="original" else "edited"
            require(text==intent[tag+"_text"] and close(point,intent[tag+"_position"]),"stored note changed the independently authored intent")
            report["records"].append({"case":case,"stage":stage,"input_sha256":digest(blob),"definition_sha256":digest(definition),
                 "text_sha256":digest(text.encode("utf-8")),"point_m":point,"semantic_checks":metrics})
    report["passed"]=len(report["records"])==4
    with args.output.open("x",encoding="utf-8",newline="\n") as stream:
        stream.write(dumps(report,indent=2,sort_keys=True)+"\n")
    print(dumps({"passed":report["passed"],"cases":len(report["records"]),"heldout_files_read":0}))


if __name__=="__main__":
    main()
