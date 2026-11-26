# model input auditing must start before project imports and caller context interpretation
KRequestAudit = """
# the audited model input must be the same file the caller pinned
KRequestPath = Path(sys.argv[2]).resolve()

# the constructor may read the packaged layout schema alongside the pinned request
KAllowed = {
    KRequestPath,
    KRoot / "src/convert/adapters/solidworks/Config/RootLayout.json",
}

# the parent process needs the actual input inventory to check replay custody
KObservedReads = set()


# repository model data and native sources must never enter the isolated constructor
def AuditModelReads(Event, Arguments):
    if Event != "open" or not isinstance(Arguments[0], (str, bytes)):
        return
    Selected = Path(fsdecode(Arguments[0])).resolve()
    Suffix = Selected.suffix.lower()
    if Selected in KAllowed:
        KObservedReads.add(str(Selected))
    elif Suffix not in (".py", ".pyc"):
        KObservedReads.add(str(Selected))
        raise AssertionError(f"unapproved model input during request replay: {Selected}")


sys.addaudithook(AuditModelReads)
"""
