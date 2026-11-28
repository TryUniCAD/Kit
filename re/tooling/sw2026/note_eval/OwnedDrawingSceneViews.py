from hashlib import sha256
from json import dumps
from pathlib import Path
from struct import unpack_from

from OwnedMessengerMemory import file_offset, require
from OwnedMessengerQueue import CORE_SHA, OwnedQueueProcess


DRAWING_SHA = "61c8481374431866f97416ce5109329f9c38e7e85b56a9f95d41bdf3122cdc47"
UI_SHA = "025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7"
GETTER_RVA = 0x6BC600
GETTER_SHA = "433f057b3a2a2d095b24323134043fd23141170ae6e582b5dd8f6974d2ebec24"
SCENE_RVA = 0x265A98
MAX_VIEWS = 64


def pointer(value):
    require(0x10000 <= value < 0x800000000000 and value % 8 == 0,
            "scene pointer is null, noncanonical or misaligned")
    return value


def role_name(value):
    return None if value is None else value.get("class_name")


class OwnedDrawingSceneProcess(OwnedQueueProcess):
    def describe(self, address, modules):
        if not address:
            return None
        table = pointer(self.word(pointer(address)))
        owner = self.owner(table, modules)
        result = {"object": hex(address), "vtable": hex(table), "vtable_owner": owner, "class_name": None}
        try:
            col = self.word(table - 8)
            base = int(owner["module"]["base"], 0)
            size = owner["module"]["image_bytes"]
            require(base <= col and col + 24 <= base + size, "RTTI locator is outside its vtable module")
            fields = unpack_from("<IIIIII", self.read(col, 24))
            require(fields[0] == 1 and fields[5] == col - base, "RTTI locator identity differs")
            row = next(row for row in modules if row["base"] == base)
            _, data, _, sections = self.identity_for(row)
            at = file_offset(fields[3] + 16, 1, sections)
            end = data.find(b"\0", at, min(at + 192, len(data)))
            require(end > at and data[at:at + 3] == b".?A", "RTTI class spelling is absent or oversized")
            result.update(class_name=data[at:end].decode("ascii"), rtti_this_offset=fields[1],
                          type_rva=hex(fields[3]), rtti_locator_rva=hex(col - base))
        except Exception as error:
            result["rtti_error"] = repr(error)
        return result

    def view(self, row, modules, cells):
        key = row["key"]
        ui = pointer(key[0])
        result = {
            "tree_node": hex(row["address"]),
            "key": {"ui_model_view": hex(ui), "mo_dr_sheet": hex(key[1]), "mo_dr_view": hex(key[2])},
            "ui_model_view": self.describe(ui, modules),
            "mo_dr_sheet": self.describe(key[1], modules),
            "mo_dr_view": self.describe(key[2], modules),
            "scene_view": self.describe(pointer(row["scene_view"]), modules),
            "layer_field_read": False,
        }
        self.partial["scene_views"]["views"].append(result)
        table = int(result["ui_model_view"]["vtable"], 0)
        getter = self.word(table + 0x5E0)
        cells[ui] = table
        cells[table + 0x5E0] = getter
        owner = self.owner(getter, modules, executable=True)
        result["getter_owner"] = owner
        qualified = (owner["module"]["name"].casefold() == "slduiu.dll"
                     and owner["module"]["sha256"] == UI_SHA and owner["rva"] == hex(GETTER_RVA))
        drawing_override = (owner["module"]["name"].casefold() == "slddrwu.dll"
                            and owner["module"]["sha256"] == DRAWING_SHA and owner["rva"] == "0x39d360"
                            and result["ui_model_view"]["class_name"] == ".?AVuiDrawingView_c@@"
                            and result["ui_model_view"].get("rtti_this_offset") == 0
                            and result["ui_model_view"]["vtable_owner"]["module"]["sha256"] == DRAWING_SHA
                            and result["ui_model_view"]["vtable_owner"]["rva"] == "0x6230e0")
        qualified = qualified or drawing_override
        result["getter_source_lane"] = "drawing override" if drawing_override else ("model-view base" if qualified else "unqualified")
        if qualified:
            body = self.read(getter, 8)
            qualified = sha256(body).hexdigest() == GETTER_SHA
            result["getter_live_sha256"] = sha256(body).hexdigest()
        result["getter_verified"] = qualified
        if qualified:
            layer = self.word(ui + 0x478)
            cells[ui + 0x478] = layer
            result.update(layer_field_read=True, layer_offset="0x478", layer_present=bool(layer),
                          layer_object=self.describe(layer, modules))
            if layer:
                layer_table = int(result["layer_object"]["vtable"], 0)
                cells[layer] = layer_table
                target = self.word(layer_table + 0x78)
                cells[layer_table + 0x78] = target
                result["invalidator_owner"] = self.owner(target, modules, executable=True)
        else:
            result["field_refusal"] = "actual uiModelView getter does not match the source-bound +0x478 leaf"
        identity = [role_name(result[name]) for name in ("ui_model_view", "mo_dr_sheet", "mo_dr_view", "scene_view")]
        identity_complete = bool(identity[0] and identity[3])
        identity_complete = identity_complete and (not key[1] or bool(identity[1])) and (not key[2] or bool(identity[2]))
        result["semantic_role_identity"] = identity
        result["semantic_identity_complete"] = identity_complete
        invalidator = result.get("invalidator_owner")
        target_identity = None if invalidator is None else {
            "name": invalidator["module"]["name"], "sha256": invalidator["module"]["sha256"],
            "rva": invalidator["rva"],
        }
        result["comparison_state"] = {
            "getter_verified": qualified, "layer_field_read": result["layer_field_read"],
            "layer_present": result.get("layer_present"), "layer_class": role_name(result.get("layer_object")),
            "invalidator": target_identity,
        }
        return result

    def scene_views(self, modules):
        candidates = [row for row in modules if Path(row["path"]).name.casefold() == "sldgfxu.dll"]
        require(len(candidates) == 1, "scene-graph module is absent or duplicated")
        module = candidates[0]
        info, _, _, _ = self.identity_for(module)
        require(info["sha256"] == CORE_SHA, "wrong exact scene-graph module")
        global_address = module["base"] + SCENE_RVA
        scene = self.word(global_address)
        if not scene:
            require(self.word(global_address) == 0, "scene-graph pointer changed during observation")
            return {"scenegraph_present": False, "views": [], "selection_ambiguous": True,
                    "node_count": 0, "semantic_groups": [], "all_layer_fields_source_verified": False,
                    "selection_reason": "no scene graph exists at this observation", "runtime_invocation_observed": False}
        pointer(scene)
        for attempt in range(1, 4):
            header = pointer(self.word(scene + 0x1E8))
            header_data = self.read(header, 32)
            leftmost, root, rightmost = unpack_from("<QQQ", header_data)
            require(header_data[0x19] != 0, "view tree header is not the native nil sentinel")
            ordered, nodes, visited = [], {}, set()
            partial = {"scenegraph_present": True, "scenegraph": hex(scene), "tree_header": hex(header),
                       "map_offset": "0x1e8", "maximum_views": MAX_VIEWS, "attempts": attempt, "views": []}
            self.partial["scene_views"] = partial

            def visit(address, parent, depth):
                if address == header:
                    return
                pointer(address)
                require(depth <= MAX_VIEWS and len(visited) < MAX_VIEWS, "view tree exceeds the bounded profile")
                require(address not in visited, "cycle or repeated node in scene-graph view tree")
                visited.add(address)
                raw = self.read(address, 64)
                require(raw[0x19] == 0, "view tree escaped into a foreign nil sentinel")
                left, actual_parent, right = unpack_from("<QQQ", raw)
                require(actual_parent == parent, "view tree parent ownership differs")
                pointer(left)
                pointer(right)
                nodes[address] = raw
                visit(left, address, depth + 1)
                key = unpack_from("<QQQ", raw, 0x20)
                ordered.append({"address": address, "key": key, "scene_view": unpack_from("<Q", raw, 0x38)[0]})
                visit(right, address, depth + 1)

            visit(pointer(root), header, 0)
            require(leftmost == (ordered[0]["address"] if ordered else header)
                    and rightmost == (ordered[-1]["address"] if ordered else header),
                    "view tree extrema disagree with its actual node traversal")
            require(len({row["key"] for row in ordered}) == len(ordered), "duplicate actual gfxViewKey in the view tree")
            cells = {}
            views = [self.view(row, modules, cells) for row in ordered]
            stable = self.word(global_address) == scene and self.word(scene + 0x1E8) == header
            stable = stable and self.read(header, 32) == header_data
            stable = stable and all(self.read(address, 64) == raw for address, raw in nodes.items())
            stable = stable and all(self.word(address) == value for address, value in cells.items())
            if not stable:
                continue
            groups = {}
            for view in views:
                key = dumps(view["semantic_role_identity"], separators=(",", ":"))
                group = groups.setdefault(key, {"identity": view["semantic_role_identity"], "states": [], "identity_complete": True})
                group["states"].append(view["comparison_state"])
                group["identity_complete"] = group["identity_complete"] and view["semantic_identity_complete"]
            for group in groups.values():
                group["instance_selection_ambiguous"] = len(group["states"]) != 1 or not group["identity_complete"]
            partial.update(node_count=len(nodes), views=views, pointer_tree_stable_during_reads=True,
                           semantic_groups=[groups[key] for key in sorted(groups)],
                           selection_basis="actual gfxViewKey roles and runtime class identities only",
                           selection_ambiguous=not views or any(group["instance_selection_ambiguous"] for group in groups.values()),
                           all_layer_fields_source_verified=bool(views) and all(view["getter_verified"] for view in views),
                           geometry_or_file_identity_from_pointer_order=False, atomic_snapshot=False,
                           runtime_invocation_observed=False)
            return partial
        raise RuntimeError("scene views changed during three bounded observations")

    def snapshot(self):
        result = super().snapshot()
        result["scene_views"] = self.scene_views(self.modules())
        result["rpm_calls_so_far"] = self.read_count
        result["rpm_bytes_so_far"] = self.read_bytes
        self.check()
        return result
