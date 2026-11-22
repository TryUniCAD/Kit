# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace
from hashlib import sha256 as DigestBytes
from io import BytesIO as ByteStream
from xml.etree import ElementTree as XmlTree
from zipfile import ZipFile

from interchange.document.Models.DocumentModel import CadDocument


# recomputed envelope hashes must not conceal a different native parameter graph
def ChangeArchive(Document: CadDocument) -> CadDocument:
    Native = next(
        Value
        for Value in Document.brep_payloads
        if Value.id == "freecad:native-document"
    )
    assert Native.data is not None
    with ZipFile(ByteStream(Native.data)) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    Scalar = RootValue.find(
        "./ObjectData/Object[@name='Extrusion']/Properties/Property[@name='LengthFwd']/Float"
    )
    assert Scalar is not None
    Scalar.set("value", "12")
    Output = ByteStream()
    with ZipFile(Output, "w") as Archive:
        Archive.writestr("Document.xml", XmlTree.tostring(RootValue, encoding="utf-8"))
    Payload = Output.getvalue()
    Binding = DigestBytes(Payload).digest()
    Payloads = tuple(
        (
            Replace(Value, data=Payload, sha256=Binding.hex())
            if Value.id == "freecad:native-document"
            else (
                Replace(Value, data=Binding, sha256=DigestBytes(Binding).hexdigest())
                if Value.id == "freecad:native-document-binding"
                else Value
            )
        )
        for Value in Document.brep_payloads
    )
    return Replace(Document, brep_payloads=Payloads)
