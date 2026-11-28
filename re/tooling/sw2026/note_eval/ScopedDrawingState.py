from math import isclose, isfinite

from AuthorPlainDrawingNotes import note_state, require
from InspectDrawingCache import drawing_tree
from ObservePlainNotePresentation01 import vector


def note_geometry(author, annotation, intent):
    note, state = note_state(author, annotation, intent, False)
    text_point = vector(author.get(note, "GetTextPoint2"), 3, "text reference point")
    require(all(isclose(x, y, abs_tol=2e-9, rel_tol=0.0)
                for x, y in zip(text_point, state["position"], strict=True)),
            "native annotation point and text point differ")
    visible = int(author.get(annotation, "Visible"))
    require(visible == 1, "native note visibility differs")
    extent = vector(author.get(note, "GetExtent"), 6, "sheet-coordinate note extent")
    require(extent[0] < extent[3] and extent[1] < extent[4], "empty native note extent")
    display = author.typed(author.get(annotation, "GetDisplayData"), "DisplayData")
    count = int(author.get(display, "GetTextCount"))
    require(0 < count <= 512, "native annotation exposes no displayed text")
    pieces = []
    for index in range(count):
        piece = {
            "text": str(author.get(display, "GetTextAtIndex", index)),
            "font": str(author.get(display, "GetTextFontAtIndex", index)),
            "position": vector(author.get(display, "GetTextPositionAtIndex", index), 3, "display text offset"),
            "height": float(author.get(display, "GetTextHeightAtIndex", index)),
            "angle": float(author.get(display, "GetTextAngleAtIndex", index)),
        }
        require(isfinite(piece["height"]) and piece["height"] > 0 and isfinite(piece["angle"]),
                "incomplete native displayed text geometry")
        pieces.append(piece)
    require("".join(piece["text"] for piece in pieces) == state["text"], "displayed and live note text differ")
    note_name = str(author.get(note, "GetName"))
    require(note_name == state["name"], "native note and annotation names differ")
    return {
        **state, "note_name": note_name, "note_text_point": text_point, "visible": visible,
        "extent": extent, "display_pieces": pieces, "dangling": False,
    }


def drawing_state(author, drawing, intent):
    drawing = author.typed(author.model, "DrawingDoc")
    names = list(author.get(drawing, "GetSheetNames"))
    require(len(names) == 1 and bool(names[0]), "drawing must have exactly one named sheet")
    sheet = author.typed(author.get(drawing, "GetCurrentSheet"), "Sheet")
    require(str(author.get(sheet, "GetName")) == names[0], "current drawing sheet is inconsistent")
    properties = vector(author.get(sheet, "GetProperties2"), 8, "native sheet properties")
    require(all(properties[index] > 0 for index in (2, 3, 5, 6)), "drawing sheet has no valid size or scale")
    require(properties[0] == 0, "native drawing paper size differs")
    sheet_view = author.typed(author.get(drawing, "GetFirstView"), "View")
    require(author.get(sheet_view, "GetNextView") is None, "drawing model view count differs")
    problems = int(author.get(author.get(author.model, "Extension"), "GetWhatsWrongCount"))
    require(problems == 0, "drawing has native rebuild errors or warnings")
    layout = {"sheet": names[0], "sheet_properties": properties, "whats_wrong": problems, "view": None}
    tree = drawing_tree(author)
    require(any(row[0] == layout["sheet"] for row in tree), "native feature tree lacks the actual active sheet")
    file_name = str(author.get(author.model, "GetPathName"))
    references = list(author.get(author.app, "GetDocumentDependencies2", file_name, True, False, False) or ())
    require(not references, "drawing contains unexpected external references")
    annotations = list(author.get(sheet_view, "GetAnnotations") or ())
    require(len(annotations) == int(intent is not None), "drawing annotation count differs")
    annotation = None if intent is None else author.typed(annotations[0], "Annotation")
    return {"sheet_view": layout, "ordered_feature_tree": tree, "model_dependencies": references,
            "annotation_count": len(annotations), "note": None if intent is None else note_geometry(author, annotation, intent)}
