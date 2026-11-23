from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordConfig import (
    KeywordConfig,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import (
    KeywordFeature,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordRef import (
    KeywordRef,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeywords import (
    MakeKeywords,
)


# a complete keyword index preserves its typed row order and classified stream grammar
@DataClass(frozen=True, slots=True)
class KeywordIndex:
    NameValue: str
    Timestamp: int
    ConfigValues: tuple[KeywordConfig, ...]
    FeatureValues: tuple[KeywordFeature | KeywordRef, ...]
    CompactTags: bool
    NativeRows: bool

    # the shared writer rebuilds the stream entirely from its typed rows and grammar
    def ToBytes(self) -> bytes:
        return MakeKeywords(
            self.NameValue,
            self.Timestamp,
            self.ConfigValues,
            self.FeatureValues,
            CompactTags=self.CompactTags,
            NativeRows=self.NativeRows,
        )
