# opening another model input would invalidate the source free request replay evidence
KRequestAudit = """
from json import dumps as WriteJson
from P03CandidateRequest import generate_request as GenerateRequest

# the audited model input must be the same file the caller pinned
KRequestPath = Path(sys.argv[2]).resolve()

# the constructor may read the packaged layout schema alongside the pinned request
KAllowed = {
    str(KRequestPath),
    str((KRoot / "src/convert/adapters/solidworks/Config/RootLayout.json").resolve()),
}

# the parent process needs the actual input inventory to check replay custody
KObservedReads = set()


# the replay claim is valid only when constructor inputs are limited to the agreed evidence
def AuditModelReads(Event, Arguments):
    if Event == "open" and isinstance(Arguments[0], (str, bytes)):
        Selected = Path(Arguments[0]).resolve()
        if Selected.suffix.lower() in (".json", ".sldprt", ".f3d"):
            assert str(Selected) in KAllowed, str(Selected)
            KObservedReads.add(str(Selected))


sys.addaudithook(AuditModelReads)
"""
