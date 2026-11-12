from pathlib import Path
from uuid import uuid4 as MakeUuid

from convert.formats.Fusion.DocumentCodec.Model.AuthorPolicy import AuthorPolicy
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.Vocabulary.ReadVocabulary import (
    ReadVocabulary,
)


def CreateAuthor(SpecValue: DocumentSpec, AssetId: str) -> AuthorState:
    Policy = AuthorPolicy()
    Source = Path(__file__).parents[1] / "Vocabulary" / "DesignClasses.json"
    Schemas = ReadVocabulary(Source)
    return AuthorState(
        SpecValue,
        Policy,
        AssetId,
        Schemas,
        {Schema.NameValue: Schema for Schema in Schemas},
        {Schema.Value.ClassGuid.upper(): Schema for Schema in Schemas},
        {},
        {},
        [],
        Policy.FirstDesignId,
        str(MakeUuid()),
        str(MakeUuid()),
        str(MakeUuid()),
        str(MakeUuid()),
        "BREP." + str(MakeUuid()) + ".smbh",
    )
