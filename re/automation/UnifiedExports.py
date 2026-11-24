import os

from SemanticComparison import DOCUMENT_BYTES, pinned_bytes
from convert.Commands.CheckFeatures import CheckFeatures
from convert.Commands.Qualified.CheckDocHistory import CheckDocHistory
from interchange.document.Models.DocumentWalk import WalkDocuments


def export_exclusions(documents):
    exclusions = {}
    for side, document in documents.items():
        try:
            for part in WalkDocuments(document):
                CheckDocHistory(part)
                CheckFeatures(part)
                if not part.bodies:
                    raise ValueError(
                        "MissingBodyHistory records have no generated design body; "
                        "retain them as comparison reports instead of unified exports"
                    )
        except ValueError as error:
            exclusions[side] = str(error)[:4096]
    return exclusions


def publish_copy(target, source, pin, unit, available):
    content = pinned_bytes(source, pin, min(DOCUMENT_BYTES, available))
    staged = target.with_suffix(".partial")
    with staged.open("xb") as writer:
        try:
            writer.write(content)
            writer.flush()
            os.fsync(writer.fileno())
        except BaseException:
            writer.close()
            staged.unlink()
            raise
    try:
        os.link(staged, target)
    finally:
        staged.unlink()
    return {
        "side": "left",
        "path": f"unified/{target.name}",
        "sha256": pin,
        "size_bytes": len(content),
        "geometry_unit": unit,
    }


def publish_unified(folder, pairs, rows, tolerances, unit, available):
    folder.mkdir(mode=0o700)
    exact = not any(tolerances.values())
    count = errors = 0
    for index, (pair, row) in enumerate(zip(pairs, rows, strict=True)):
        row["unified"] = None
        if (
            not exact
            or row["status"] != "equal_observed_graph"
            or row["counts"]["source_issues"]
            or row.get("unified_exclusions")
        ):
            continue
        try:
            copy = publish_copy(
                folder / f"{index:04d}.json",
                pair["left"],
                row["input_sha256"]["left"],
                unit,
                available,
            )
        except (OSError, ValueError) as error:
            row["unified_error"] = str(error)[:4096]
            errors += 1
            continue
        available -= copy["size_bytes"]
        row["unified"] = copy
        count += 1
    return {
        "policy": "exact_equal_observed_graph",
        "exact_tolerances": exact,
        "count": count,
        "errors": errors,
    }
