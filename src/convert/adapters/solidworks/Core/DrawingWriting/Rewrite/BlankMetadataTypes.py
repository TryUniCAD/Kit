from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Header.HeaderInput import (
    HeaderInput,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.HistoryInput import (
    HistoryInput,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Presentation.StyleInput import (
    StyleInput,
)
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import (
    ModelDefSettings,
)
from convert.adapters.solidworks.Drawing.Construction.Model.DrawFolders import (
    DrawFolders,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.BlankDrawInput import (
    BlankDrawInput,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.DrawDocOptions import (
    DrawDocOptions,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetNames import SheetNames
from interchange.document.Models.Drawing.DrawingData import DrawingData
from interchange.document.Models.Drawing.DrawingSheet import DrawingSheet

# structured native metadata may restore only the already qualified semantic construction owners
KBlankMetadataTypes = frozenset(
    (
        SelfFileInput,
        HeaderInput,
        HistoryInput,
        FeatureTarget,
        StyleInput,
        UnitInput,
        ModelDefSettings,
        DrawFolders,
        BlankDrawInput,
        DrawDocOptions,
        SheetNames,
        DrawingData,
        DrawingSheet,
    )
)
