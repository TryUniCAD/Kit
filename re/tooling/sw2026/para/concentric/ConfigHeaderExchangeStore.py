from ConfigHeaderExchangeModel import (
    CONFIG_HEADER_STREAM,
    config_header_cell,
    project_active_config,
    project_config_header,
)

from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHeader import ReadMgrHeader
from convert.adapters.solidworks.Archive.Exchange.DatabaseClock import (
    EncodeDbClock,
)
from convert.adapters.solidworks.Archive.Exchange.WriteUnqlite import (
    WriteUnqlite,
)

CMGR_HEADER = "Contents/CMgrHdr2"
VERSION = 19000


def add_config_header_exchange(streams, manager, created, identity):
    if CONFIG_HEADER_STREAM in streams:
        raise ValueError("configuration exchange already has an owner")
    directory = ReadMgrHeader(streams[CMGR_HEADER], VERSION).RootValue
    rows = directory.FieldsValue["f08"]["items"]
    if len(rows) != 1:
        raise ValueError("configuration exchange requires one actual lightweight entry")
    config = project_config_header(rows[0]["o"], project_active_config(manager))
    record = config_header_cell(config, identity)
    store = WriteUnqlite(EncodeDbClock(created), (record,))
    return streams | {CONFIG_HEADER_STREAM: store}
