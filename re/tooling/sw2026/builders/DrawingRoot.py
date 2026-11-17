from __future__ import annotations

from Core import Obj
from builders.DrawingSheetObjects import empty_drawing_sheet
from builders.DrawingTail import drawing_feature_filetime, empty_drawing_tail
from builders.Metadata import fields
from builders.Model import clear_model_update, detail_cabinet, feature, folder, model_fields, node_list, object_list, relation_manager, unit_component


_FOLDER_NAMES = ("annotations", "binder", "comments", "blocks", "ink_markups", "review_markups")


def _transient_folder(*, cls, name, model, created_at, target):
    node = feature(cls=cls, owner=model, name=name, allocator=None, **target)
    node.f.update({**drawing_feature_filetime(created_at), "f360": 1, "f370": 0})
    return node


def empty_drawing_root(*, name, allocator, settings, folder_names, sheet_names, detail_definitions, document_units,
                       auto_dim_text_link, block_identity, created_at, date_code, parasolid_version):
    names = fields(folder_names, "drawing folders", _FOLDER_NAMES)
    sheet_names = fields(sheet_names, "drawing sheet support names", ("plane_name", "profile_name", "detail_name"))
    target = {"date_code": date_code, "parasolid_version": parasolid_version}
    model = Obj("moDrawing_c")
    base = model_fields(
        node=model, name=name, allocator=allocator, detail_definitions=detail_definitions,
        document_units=document_units, analysis_units=None, self_component=unit_component(owner=model),
        relation_graph=relation_manager(owner=model),
    )
    base.update({"f78": None, **{key: Obj("suObList", object_list()) for key in ("f9d8", "fa48", "fa50")}})
    clear_model_update(model=model)
    cabinet = detail_cabinet(owner=model, name=names["annotations"], allocator=allocator, **target)
    persistent = {"owner": model, "allocator": allocator, "created_at": created_at, **target}
    binder = folder(cls="moDocsFolder_c", name=names["binder"], **persistent)
    comments = folder(cls="moCommentsFolder_c", name=names["comments"], **persistent)
    sheet = empty_drawing_sheet(settings=settings, owner=model, allocator=allocator, created_at=created_at,
                                **sheet_names, **target)
    ink = folder(cls="moInkMarkupFolder_c", name=names["ink_markups"], **persistent)
    blocks = _transient_folder(cls="moBlockFolder_c", name=names["blocks"], model=model, created_at=created_at, target=target)
    reviews = _transient_folder(cls="moMarkupCommentFolder_c", name=names["review_markups"], model=model,
                                created_at=created_at, target=target)
    children = (comments, blocks, binder, cabinet, ink, reviews, sheet)
    for node in children[:-1]:
        node["f0c"] &= 0xFFFD7FF8
    base["f60"] = node_list(children)
    base.update(empty_drawing_tail(owner=model, active_sheet=sheet, auto_dim_text_link=auto_dim_text_link,
                                   block_identity=block_identity, created_at=created_at, **target))
    return model
