# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from io import BytesIO as ByteStream
from xml.etree import ElementTree as XmlTree
from zipfile import ZipFile

from tests.Research.Archives.FreeCadAliases.NativeAliasTests import MakeFixture


# sheet only archives preserve the previously accepted exact native replay boundary
def MakeReplay(CaseName: str) -> bytes:
    Payload = MakeFixture("literal")
    if CaseName != "supported":
        return Payload
    with ZipFile(ByteStream(Payload)) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    for GroupName in ("Objects", "ObjectData"):
        Group = RootValue.find(GroupName)
        assert Group is not None
        Owner = Group.find("./Object[@name='Extrusion']")
        assert Owner is not None
        Group.remove(Owner)
        Group.set("Count", str(len(Group)))
    Output = ByteStream()
    with ZipFile(Output, "w") as Archive:
        Archive.writestr("Document.xml", XmlTree.tostring(RootValue, encoding="utf-8"))
    return Output.getvalue()
