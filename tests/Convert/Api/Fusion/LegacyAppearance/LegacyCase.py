from pathlib import Path as FilePath


# authored values must reach the child through a standalone persisted request
def LegacyCase(Folder: FilePath) -> FilePath:
    Folder.mkdir()
    Request = Folder / "Request.json"
    Source = FilePath(__file__).with_name("AuthoredRequest.json")
    _ = Request.write_bytes(Source.read_bytes())
    assert tuple(Folder.iterdir()) == (Request,)
    return Request
