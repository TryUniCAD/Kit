from io import BytesIO as ByteStream
from zipfile import ZipFile


# a native link in the same directory populates the shared parent replay scope
def MakePadParent() -> bytes:
    DocumentXml = b"""<Document SchemaVersion="4" ProgramVersion="1.1.0" FileVersion="1">
  <Objects Count="1"><Object type="App::Link" name="Link" id="1"/></Objects>
  <ObjectData Count="1"><Object name="Link"><Properties Count="1">
    <Property name="LinkedObject" type="App::PropertyXLink">
      <XLink file="Child.FCStd" name="Boss"/>
    </Property>
  </Properties></Object></ObjectData>
</Document>"""
    Output = ByteStream()
    with ZipFile(Output, "w") as Archive:
        Archive.writestr("Document.xml", DocumentXml)
    return Output.getvalue()
