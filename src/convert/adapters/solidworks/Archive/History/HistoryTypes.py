from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

# biography uses its own base one class and object map
KBioRootClass = RuntimeClass("moBiography_c", 1)

# version history starts with its own concrete runtime class
KVersionHistClass = RuntimeClass("moVersionHistory_c", 1)

# each version state links a separately tagged date code history
KDateHistClass = RuntimeClass("moDateCodeHistory_c", 1)

# the two physical streams admit only these top level runtime owners
KHistoryRootTypes = (KBioRootClass, KVersionHistClass)
