# generic native feature constructors clear these independent words without borrowing completed save state
KFeatureWords = (
    "f298",
    "f28c",
    "f2a8",
    "f2b8",
    "f2bc",
    "f1f4",
    "f2ec",
    "fa8",
    "f208",
    "f318",
    "f2a4",
    "f2a0",
    "f34c",
)

# generic native feature constructors leave these independent owned references absent
KFeatureRefs = ("f258", "f2f0")

# empty native strings remain independently owned even when their constructor payloads agree
KFeatureTexts = ("f1f8", "f200")
