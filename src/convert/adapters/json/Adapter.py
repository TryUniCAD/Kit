# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.adapters.json.Metadata import JsonMetadata
from convert.adapters.json.Reader import JsonReader
from convert.adapters.json.Writer import JsonWriter


# this adapter composes focused reading writing and metadata responsibilities
class JsonAdapter(JsonMetadata, JsonReader, JsonWriter):
    KAdapterSlots = ()

    locals()["__slots__"] = KAdapterSlots
