# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from interchange.brep.topology.BrepModel import BrepModel


# independent results preserve their distinct body topology in the same component document
def JoinRevModels(Models: tuple[BrepModel, ...]) -> BrepModel:
    return BrepModel(
        curves=tuple(ItemValue for Model in Models for ItemValue in Model.curves),
        pcurves=tuple(ItemValue for Model in Models for ItemValue in Model.pcurves),
        surfaces=tuple(ItemValue for Model in Models for ItemValue in Model.surfaces),
        vertices=tuple(ItemValue for Model in Models for ItemValue in Model.vertices),
        edges=tuple(ItemValue for Model in Models for ItemValue in Model.edges),
        coedges=tuple(ItemValue for Model in Models for ItemValue in Model.coedges),
        loops=tuple(ItemValue for Model in Models for ItemValue in Model.loops),
        wires=tuple(ItemValue for Model in Models for ItemValue in Model.wires),
        faces=tuple(ItemValue for Model in Models for ItemValue in Model.faces),
        face_uses=tuple(ItemValue for Model in Models for ItemValue in Model.face_uses),
        shells=tuple(ItemValue for Model in Models for ItemValue in Model.shells),
        shell_uses=tuple(
            ItemValue for Model in Models for ItemValue in Model.shell_uses
        ),
        regions=tuple(ItemValue for Model in Models for ItemValue in Model.regions),
        bodies=tuple(ItemValue for Model in Models for ItemValue in Model.bodies),
    )
