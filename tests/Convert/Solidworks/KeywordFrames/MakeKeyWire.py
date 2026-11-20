# the attribute must preserve delimiter text and line endings during compaction
KKeywordName = 'A /> & "mode" < \u03bb\rattr\r\nline'

# authored character data must survive the same compact framing
KKeywordText = "\u03c0 /> & <\rtext\r\nline"

# text following a child must retain its own line endings through framing
KKeywordTail = " tail />\rtail\r\nline"


# the expected markup specifies entity escapes and the empty delimiter independently
def MakeKeyWire(IsCompact: bool) -> bytes:
    Ending = "/>" if IsCompact else " />"
    Content = (
        '<Keywords id="17" Name="A /&gt; &amp; &quot;mode&quot; &lt; \u03bb&#13;attr&#13;&#10;line">'
        + '<Configuration id="0" Name="Default" Type="ConfigurationManager" Material=""'
        + Ending
        + '<Feature id="7" Name="Sketch1" Type="ProfileFeature">'
        + '<Dimension Name="D1">\u03c0 /&gt; &amp; &lt;&#13;text&#13;\nline</Dimension>'
        + " tail /&gt;&#13;tail&#13;\nline</Feature></Keywords>"
    )
    return (
        b'\x86<?xml version="1.0" encoding="UTF-8"?>\r\n'
        + Content.encode("utf-8")
        + b"\r\n"
    )
