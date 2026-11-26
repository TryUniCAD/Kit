# model input auditing must start before project imports and caller context interpretation
KRequestAudit = """
# the audited model input must be the same file the caller pinned
KRequestPath = Path(sys.argv[2]).resolve()

# publication may stage only next to the explicit candidate selected by the parent
KCandidatePath = Path(sys.argv[4]).resolve() if sys.argv[4] else None

# the output is unavailable as a model input until generation has finished
KOutputReadEnabled = False

# the constructor may read the packaged layout schema alongside the pinned request
KAllowed = {
    KRequestPath,
    KRoot / "src/convert/adapters/solidworks/Config/RootLayout.json",
}

# the parent process needs the actual input inventory to check replay custody
KObservedReads = set()


# the isolated constructor may read the pinned model and stage only its requested candidate
def AuditModelReads(Event, Arguments):
    if Event != "open" or not isinstance(Arguments[0], (str, bytes)):
        return
    Selected = Path(fsdecode(Arguments[0])).resolve()
    if Arguments[2] & (O_CREAT | O_RDWR | O_WRONLY):
        if KCandidatePath is not None and (
            Selected == KCandidatePath.parent
            or (
                Selected.parent == KCandidatePath.parent
                and Selected.name.startswith(".kit-fresh-boss-")
            )
        ):
            return
        raise AssertionError(f"unapproved write during request replay: {Selected}")
    if KOutputReadEnabled and Selected == KCandidatePath:
        return
    Suffix = Selected.suffix.lower()
    if Selected in KAllowed:
        KObservedReads.add(str(Selected))
    elif Suffix not in (".py", ".pyc"):
        KObservedReads.add(str(Selected))
        raise AssertionError(f"unapproved model input during request replay: {Selected}")


sys.addaudithook(AuditModelReads)
"""
