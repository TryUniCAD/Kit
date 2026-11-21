from pathlib import Path as FilePath
from sys import argv as ProcessArgs

from convert import open_document as OpenDocument


# public reader evidence must cross the sdk entry point with vendor geometry dependencies excluded
def MainEntry() -> None:
    Document = OpenDocument(
        FilePath(ProcessArgs[1]), include_brep=False, include_tessellation=False
    )
    print(Document.to_json(indent=None))


if __name__ == "__main__":
    MainEntry()
