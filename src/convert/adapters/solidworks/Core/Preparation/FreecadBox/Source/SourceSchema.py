# these source fields identify the ordinary attached additive box vocabulary
KFeatureProps = frozenset(
    (
        "AddSubShape",
        "AttacherType",
        "AttachmentOffset",
        "BaseFeature",
        "ExpressionEngine",
        "Height",
        "Label",
        "Label2",
        "Length",
        "MapMode",
        "MapPathParameter",
        "MapReversed",
        "Placement",
        "Refine",
        "Shape",
        "Support",
        "Visibility",
        "Width",
    )
)

# later releases name the attachment owner and add material and suppression fields
KNewFeatProps = frozenset(
    (
        "AttacherEngine",
        "AttachmentSupport",
        "ShapeMaterial",
        "Suppressed",
        "SuppressedShape",
    )
)

# these source scalars must belong to the same primitive rather than come from other owners
KFeatureScalars = frozenset(
    (
        "AttacherType",
        "Height",
        "Label",
        "Label2",
        "Length",
        "MapMode",
        "MapPathParameter",
        "MapReversed",
        "Refine",
        "Visibility",
        "Width",
    )
)

# the body properties define ownership of the single feature and its origin
KBodyProps = frozenset(
    (
        "BaseFeature",
        "ExpressionEngine",
        "Group",
        "Label",
        "Label2",
        "Origin",
        "Placement",
        "Shape",
        "Tip",
        "Visibility",
    )
)

# validated document properties distinguish authored values from transient placeholders
KDocProps = frozenset(
    (
        "FileName",
        "Tip",
        "TransientDir",
        "Comment",
        "Company",
        "CreatedBy",
        "CreationDate",
        "Id",
        "Label",
        "LastModifiedBy",
        "LastModifiedDate",
        "License",
        "LicenseURL",
        "Material",
        "Meta",
        "ShowHidden",
        "TipName",
        "Uid",
    )
)

# dimensional driver order follows the length width and height owners of the source primitive
KDimensions = ("Length", "Width", "Height")

# actual source plane names bind to the named archive objects and principal basis
KPlaneFrames = {
    "XY-plane": ("XY_Plane", 0, ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))),
    "XZ-plane": ("XZ_Plane", 1, ((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0))),
    "YZ-plane": ("YZ_Plane", 2, ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0))),
}

# extension order is part of the measured source attachment owner layouts
KReleaseExts = {
    "0.21": ("AttachExtension",),
    "1.0": ("SuppressibleExtension", "AttachExtension"),
    "1.1": ("SuppressibleExtension", "AttachExtension", "PreviewExtension"),
}

# both newer measured releases use the library default material with the same source identifier
KDefaultMat = "7f9fd73b-50c9-41d8-b7b2-575a030c1eeb"
