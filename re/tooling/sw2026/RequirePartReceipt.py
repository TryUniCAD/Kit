from io import BytesIO

from convert import write_document
from convert.adapters.base.WriteOptions import WriteOptions


def must_need_receipt(action):
    try:
        action()
    except ValueError as error:
        if "offline native measurement receipt" not in str(error):
            raise
    else:
        raise ValueError("an unmeasured document reached native publication")


def measure_refusals(document, path, locator, writer, audit):
    format_id = "solidworks.sldprt"
    policy = {"require_native_transfers": True}
    stream_policy = {**policy, "final_destination": locator}
    sentinel = path.read_bytes()
    stream = BytesIO()
    new_path = path.parent.parent / "unmeasured" / path.name
    with audit.active("memory"):
        must_need_receipt(lambda: write_document(
            document, stream, destination_format=format_id, allow_carrier=False, values=stream_policy,
        ))
        must_need_receipt(lambda: writer.write(document, stream, WriteOptions(values=stream_policy)))
    with audit.active("path"):
        must_need_receipt(lambda: write_document(
            document, path, destination_format=format_id, overwrite=True, allow_carrier=False, values=policy,
        ))
        must_need_receipt(lambda: writer.write(document, new_path, WriteOptions(values=policy)))
    if (
        path.read_bytes() != sentinel
        or tuple(path.parent.iterdir()) != (path,)
        or new_path.parent.exists()
        or stream.getvalue()
        or stream.tell()
    ):
        raise ValueError("a refused part write touched the file, stream or unstaged directory")
    return 4
