from json import dumps as DumpJson
from pathlib import Path as FilePath

from tests.Convert.Solidworks.KeywordFrames.RunKeywordFrame import RunKeywordFrame


# the xml prefix and actual explicit declarations must survive both lexical forms
def TestNamespaces(TmpPath: FilePath) -> None:
    for CompactMode in (True, False):
        Source = TmpPath / f"namespace{CompactMode}.json"
        Output = Source.with_suffix(".bin")
        _ = Source.write_text(
            DumpJson(
                {
                    "root": "Keywords",
                    "compact": CompactMode,
                    "name": "Part",
                    "text": "child",
                    "tail": "after",
                    "literal_namespace": True,
                }
            ),
            encoding="utf-8",
        )
        Written = RunKeywordFrame("write", Source, Output)
        assert Written.returncode == 0, Written.stderr
        Wire = Output.read_bytes()
        assert b'xmlns:kit="urn:kit:declared"' in Wire
        assert b'xml:lang="en"' in Wire
        assert b'kit:role="feature"' in Wire
        Read = RunKeywordFrame("read", Output, Source.with_suffix(".result"))
        assert Read.returncode == 0, Read.stderr
