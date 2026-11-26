# KeyWords text preserves carriage returns

A literal CR or CRLF in serialized element text or a child tail reads
back as LF. XML 1.0 normalizes these sequences before parsing. A numeric
character reference carries the original CR through that stage.
[XML 1.0 end-of-line handling](https://www.w3.org/TR/xml/#sec-line-ends)

`FrameKeywords` writes `&#13;` for each literal CR in the XML payload.
A CRLF in text or a tail keeps its LF after the numeric reference.
The frame adds its own CRLF pairs after that substitution. ElementTree
already escapes attribute CR and LF as numeric references. Both empty
tag styles use the same text handling.
[Independent process case](../../../../../../tests/Convert/Solidworks/KeywordFrames/KeywordModelTests.py)
