from io import BytesIO as ByteStream
from zipfile import ZipFile


# authored profile and cached length values distinguish ownership from matching geometry
def MakePadFixture(CaseName: str) -> bytes:
    DepthValue = "17" if CaseName == "stale" else "16"
    ObjectName = "Caption" if CaseName == "label" else "Layout"
    Expression = f"{ObjectName}.Constraints.span / 3"
    Constraint = '<Constrain Type="6" Name="span" Value="48" First="0" />'
    ConstraintRows = Constraint * (2 if CaseName == "duplicate" else 1)
    ProfileLink = (
        '<LinkSub count="1" value="Layout"><Sub value="Edge1"/></LinkSub>'
        if CaseName == "subelement"
        else '<LinkSub count="0" value="Layout"/>'
    )
    DocumentXml = f"""<Document SchemaVersion="4" ProgramVersion="1.1.0" FileVersion="1">
  <Objects Count="2">
    <Object type="Sketcher::SketchObject" name="Layout" id="1"/>
    <Object type="PartDesign::Pad" name="Boss" id="2"/>
  </Objects>
  <ObjectData Count="2">
    <Object name="Layout"><Properties Count="3">
      <Property name="Label" type="App::PropertyString"><String value="Caption"/></Property>
      <Property name="Geometry" type="Part::PropertyGeometryList"><GeometryList count="1">
        <Geometry type="Part::GeomLineSegment">
          <LineSegment StartX="0" StartY="0" StartZ="0" EndX="48" EndY="0" EndZ="0"/>
        </Geometry>
      </GeometryList></Property>
      <Property name="Constraints" type="Sketcher::PropertyConstraintList"><ConstraintList>
        {ConstraintRows}
      </ConstraintList></Property>
    </Properties></Object>
    <Object name="Boss"><Properties Count="3">
      <Property name="Profile" type="App::PropertyLinkSub">{ProfileLink}</Property>
      <Property name="Length" type="App::PropertyLength"><Float value="{DepthValue}"/></Property>
      <Property name="ExpressionEngine" type="App::PropertyExpressionEngine">
        <ExpressionEngine count="1"><Expression path="Length" expression="{Expression}"/></ExpressionEngine>
      </Property>
    </Properties></Object>
  </ObjectData>
</Document>"""
    Output = ByteStream()
    with ZipFile(Output, "w") as Archive:
        Archive.writestr("Document.xml", DocumentXml.encode("utf-8"))
    return Output.getvalue()
