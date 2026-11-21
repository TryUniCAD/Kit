from convert import open_document as OpenDoc


# unsupported histories and present corrupt caches must keep their strict failure instead of receiving a plausible substitute body
def RejectPrism(BytesValue: bytes) -> None:
    try:
        _ = OpenDoc(BytesValue, source_format="solidworks.sldprt")
    except ValueError as ErrorInfo:
        assert "no readable Parasolid payload" in str(ErrorInfo)
    else:
        raise AssertionError("strict read accepted an unqualified cache free model")
