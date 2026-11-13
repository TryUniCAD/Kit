from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DrawingCodec.Author.Defaults.DrawingPolicy import (
    KLargeThumb,
    KPreviewSide,
    KSheetSizes,
    KTemplateSheet,
    KThumbSmall,
)
from convert.formats.Fusion.DrawingCodec.Author.Members.SheetPainter import (
    SheetImage,
)
from convert.formats.Fusion.DrawingCodec.Model.DrawingNames import KImageFolders


def BuildImages(SheetId: str, SheetSize: str) -> tuple[ContainerPart, ...]:
    SheetWidth, SheetHeight = KSheetSizes[SheetSize][:2]
    Aspect = SheetWidth / SheetHeight
    Previews, Thumbnails = KImageFolders
    Images = (
        (Thumbnails + KTemplateSheet + "_large.png", KLargeThumb),
        (Thumbnails + SheetId + "_large.png", KLargeThumb),
        (Thumbnails + SheetId + "_small.png", KThumbSmall),
        (Thumbnails + KTemplateSheet + "_small.png", KThumbSmall),
        (Previews + "small.png", (KPreviewSide, KPreviewSide)),
    )
    return tuple(
        ContainerPart(NameValue, SheetImage(Width, Height, Aspect))
        for NameValue, (Width, Height) in Images
    )
