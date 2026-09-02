"""Dress the 4 x 4 m Room B and shared Door without changing Interaction."""

import sys
from pathlib import Path

import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
import room_a_assets as apartment


ART = "/Game/Environment/RoomB"
ACTORS = apartment.ACTORS


def material(name):
    result = unreal.load_asset(apartment.ART + "/Materials/M_" + name)
    apartment.require(result, f"Missing shared apartment material: {name}")
    return result


def room_b(item):
    if isinstance(item, list):
        return [room_b(part) for part in item]
    item.set_editor_property("tags", [unreal.Name("RoomBArt")])
    return item


def box(name, location, size, surface, collision=True):
    return room_b(apartment.box("RoomB_" + name, location, size, surface, collision))


def mesh(name, asset, location, scale=(1, 1, 1), yaw=0, collision=True):
    return room_b(apartment.mesh_actor("RoomB_" + name, asset, location, scale, yaw, collision=collision))


def exterior_box(name, location, size, surface, layer):
    return apartment.exterior_box("RoomB_" + name, location, size, surface, layer,
                                  room_tag="RoomBExterior", art_tag="RoomBArt")


def exterior_mesh(name, asset, location, scale, surface, layer):
    return apartment.exterior_mesh("RoomB_" + name, asset, location, scale, surface, layer,
                                   room_tag="RoomBExterior", art_tag="RoomBArt")


def exterior_model(name, asset, location, scale, layer, yaw=0):
    return apartment.exterior_mesh("RoomB_" + name, asset, location, scale, None, layer, yaw,
                                   room_tag="RoomBExterior", art_tag="RoomBArt")


def build_room_b():
    apartment.require(unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level("/Game/Maps/L_Testbed"), "Map not found")
    existing = {item.get_actor_label(): item for item in ACTORS.get_all_level_actors()}
    for item in existing.values():
        if item.actor_has_tag("RoomBArt") or item.get_actor_label() in ("RoomB_BlockoutLight", "RoomB_EastWall"):
            ACTORS.destroy_actor(item)
    oak, wall, trim = material("Oak"), material("WarmPlaster"), material("Trim")
    sage, bronze, dark = material("SagePaint"), material("Bronze"), material("Charcoal")
    linen, paper = material("Linen"), material("Paper")
    slots = {name: material(name) for name in ("Oak", "Linen", "Rug", "Piping", "Bronze", "Shade")}
    authored = {name: apartment.model(name, True, ART) for name in
                ("SM_WritingDesk", "SM_DeskChair", "SM_GuestDaybed", "SM_Bookcase")}
    for asset in authored.values():
        for index, slot in enumerate(asset.get_editor_property("static_materials")):
            apartment.require(str(slot.material_slot_name) in slots, "Unknown Room B material slot")
            asset.set_material(index, slots[str(slot.material_slot_name)])

    # Shared partition's east face is x=20. Its thickness is excluded from the
    # 400 cm clear footprint; all other wall thickness grows outward.
    for label, location, size, surface in (
            ("RoomB_Floor", (220, 0, -10), (400, 400, 20), material("Floor")),
            ("RoomB_Ceiling", (220, 0, 280), (420, 440, 20), material("Ceiling")),
            ("RoomB_NorthWall", (220, 210, 135), (420, 20, 270), wall),
            ("RoomB_SouthWall", (220, -210, 135), (420, 20, 270), sage)):
        item = existing[label]
        item.set_actor_location(unreal.Vector(*location), False, False)
        item.set_actor_scale3d(unreal.Vector(*(value / 100 for value in size)))
        item.static_mesh_component.set_material(0, surface)
    # East-facing window, no outdoor playable geometry. The same courtyard
    # plaster, dark frames, sill profile, and warm trim continue Room A.
    for y in (-165, 165):
        box("WindowWall_Pier", (430, y, 135), (20, 70, 270), wall)
    box("WindowWall_Sill", (430, 0, 40), (20, 260, 80), wall)
    box("WindowWall_Head", (430, 0, 256), (20, 260, 28), wall)
    box("Window_Sill", (417, 0, 81), (34, 268, 4), trim)
    for y in (-130, 0, 130):
        box("Window_Mullion", (427, y, 161), (9, 5, 162), dark)
    for z in (83, 240):
        box("Window_Rail", (427, 0, z), (9, 265, 5), dark)
    barrier = box("Window_InvisibleBarrier", (435, 0, 161), (2, 260, 160), dark)
    barrier.set_actor_hidden_in_game(True)
    barrier.static_mesh_component.set_cast_shadow(False)
    exterior(box("Courtyard_Parapet", (600, 0, 90), (20, 850, 180), wall),
             "ExteriorForeground")
    exterior(box("Courtyard_Coping", (600, 0, 182), (27, 870, 6), trim),
             "ExteriorForeground")
    # The quieter east courtyard uses the same plaster, stone, charcoal frames,
    # and late-afternoon warmth as Room A, but its enclosing residential facade
    # and planted parapet make the view immediately distinct.
    exterior_plaster = material("ExteriorPlaster")
    exterior_stone = material("ExteriorStone")
    exterior_glass = material("ExteriorGlass")
    exterior_warm = material("ExteriorWarmWindow")
    exterior_distant = material("ExteriorDistant")
    for y in (-255, 245):
        exterior_box("Courtyard_Planter", (680, y, 207), (70, 130, 42), exterior_stone,
                     "ExteriorForeground")
    courtyard_plant = apartment.model("potted_plant_02")
    for index, (x, y, scale, yaw) in enumerate((
            (660, -265, (1.20, 1.20, 1.20), 15),
            (675, 245, (1.05, 1.05, 1.05), -20))):
        exterior_model(f"Courtyard_Greenery_{index}", courtyard_plant, (x, y, 190),
                       scale, "ExteriorForeground", yaw)
    exterior_box("Courtyard_Facade", (1030, 0, 80), (46, 920, 440), exterior_plaster,
                 "ExteriorMiddleDistance")
    exterior_box("Courtyard_LeftReturn", (835, -470, 80), (430, 30, 440), exterior_stone,
                 "ExteriorMiddleDistance")
    exterior_box("Courtyard_RightReturn", (835, 470, 80), (430, 30, 440), exterior_stone,
                 "ExteriorMiddleDistance")
    exterior_box("Courtyard_Cornice", (1003, 0, 300), (8, 940, 12), trim,
                 "ExteriorMiddleDistance")
    # Recessed dark surrounds, inset glazing, mullions, and sills break up the
    # neighbouring facade at a believable residential scale.
    for y in (-285, -95, 95, 285):
        for z, window_surface in ((75, exterior_glass), (220, exterior_warm if y == 95 else exterior_glass)):
            exterior_box("Courtyard_WindowReveal", (1005.5, y, z), (3, 112, 102), dark,
                         "ExteriorMiddleDistance")
            exterior_box("Courtyard_WindowGlass", (1003.5, y, z), (2, 92, 82), window_surface,
                         "ExteriorMiddleDistance")
            exterior_box("Courtyard_WindowMullion", (1001.8, y, z), (2, 5, 82), dark,
                         "ExteriorMiddleDistance")
            exterior_box("Courtyard_WindowSill", (1001.5, y, z - 53), (5, 122, 5), trim,
                         "ExteriorMiddleDistance")
    # Roofs beyond the low courtyard facade keep a readable horizon and reuse
    # Room A's restrained cool-distance treatment.
    for index, (x, y, width, depth, height) in enumerate((
            (1710, -430, 340, 330, 430), (1840, 0, 430, 360, 520),
            (1680, 450, 300, 300, 380))):
        exterior_box(f"Courtyard_DistantBlock_{index}", (x, y, height / 2 - 120),
                     (width, depth, height), exterior_distant, "ExteriorDistant")
    for y in (-198.75, 198.75):
        box("Skirting", (220, y, 5), (400, 2.5, 10), trim)
    box("East_Skirting", (418.75, 0, 5), (2.5, 400, 10), trim)
    for y in (-125, 125):
        box("West_Skirting", (21.25, y, 5), (2.5, 150, 10), trim)
    # Matching casing on the guest-room side and a flush threshold, not a step.
    for y in (-55, 55):
        box("Door_Casing", (24, y, 108), (5, 9, 216), trim, False)
    box("Door_CasingHead", (24, 0, 216), (5, 119, 9), trim, False)
    box("Door_Threshold", (10, 0, .35), (20, 99, .7), oak, False)
    # Reverse handle follows the same tested leaf; it cannot block the capsule.
    leaf = existing["Door"].get_component_by_class(unreal.StaticMeshComponent)
    handle = box("Door_Handle", (10, -32, 102), (8, 14, 2), bronze, False)
    handle.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    handle.attach_to_component(leaf, "", unreal.AttachmentRule.KEEP_WORLD,
                               unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)

    # Keep the 90-degree Door swing and the central approach to NPC B clear.
    # glTF's baked conversion maps authored +Y (furniture backs) to Unreal -Y.
    mesh("WritingDesk", authored["SM_WritingDesk"], (300, 168, 0), yaw=180)
    mesh("DeskChair", authored["SM_DeskChair"], (280, 100, 0))
    mesh("GuestDaybed", authored["SM_GuestDaybed"], (235, -151, 0))
    mesh("Bookcase", authored["SM_Bookcase"], (63, 181, 0), yaw=180)
    mesh("BedsideTable", apartment.model("modern_coffee_table_01"), (382, -151, 0), (.42, .42, 1))
    mesh("GuestRug", apartment.model("SM_Rug", True), (222, -32, 0), (.70, .48, 1), collision=False)
    mesh("ReadingLamp", apartment.model("SM_FloorLamp", True), (71, -169, 0))
    mesh("DeskVase", apartment.model("ceramic_vase_03"), (373, 177, 77.1), (.46, .46, .46), collision=False)
    mesh("WindowPlant", apartment.model("potted_plant_02"), (390, 102, 0), (.65, .65, .65))
    box("Notebook", (355, 153, 78), (20, 15, 1.6), sage, False)
    box("Notebook_Pages", (355, 152.7, 78.1), (19.4, 14.8, 1), paper, False)
    box("Pen", (345, 150, 79.2), (1, 12, .8), bronze, False)
    box("GuestBook", (382, -151, 40), (20, 15, 2), material("Ochre"), False)
    # Two original geometric prints echo the living-room diptych.
    for x, surface in ((198, sage), (278, material("Ochre"))):
        box("Art_Frame", (x, -195, 173), (63, 4, 76), oak, False)
        box("Art_Mat", (x, -192.7, 173), (58, .8, 71), paper, False)
        box("Art_Field", (x - 5, -192.1, 168), (30, .3, 43), surface, False)
        circle = room_b(apartment.mesh_actor("RoomB_Art_Circle", unreal.load_asset("/Engine/BasicShapes/Cylinder"),
                                            (x + 4, -191.7, 188), (.26, .26, .003), material=bronze, collision=False))
        circle.set_actor_rotation(unreal.Rotator(roll=90), False)
    # Physical shelf and pinboard dress the office above the workstation.
    box("Pinboard_Frame", (291, 196, 166), (130, 4, 63), oak, False)
    box("Pinboard_Linen", (291, 193.7, 166), (125, 1, 58), linen, False)
    for x, z, width in ((252, 168, 21), (283, 175, 18), (319, 164, 26)):
        box("Pinboard_Note", (x, 193, z), (width, .3, 22), paper, False)
    box("OfficeShelf", (290, 181, 211), (154, 33, 3), oak, False)
    for x in (225, 355):
        box("ShelfBracket", (x, 191, 201), (3, 13, 18), bronze, False)
    for i in range(5):
        box("ShelfBook", (247 + i * 5, 184, 222 + i % 2), (4, 16, 19 + i % 2 * 2),
            (sage, paper, dark)[i % 3], False)
    existing["NPC_B"].set_actor_location(unreal.Vector(310, 25, 90), False, False)
    light = room_b(apartment.actor(unreal.RectLight, "RoomB_WindowDaylight", (410, 0, 178), (0, 180, 0))).get_component_by_class(unreal.RectLightComponent)
    light.set_mobility(unreal.ComponentMobility.MOVABLE)
    # Lift the window-facing resident without flattening the warm interior.
    for key, value in (("intensity_units", unreal.LightUnits.LUMENS), ("intensity", 2800.),
                       ("source_width", 240.), ("source_height", 140.), ("attenuation_radius", 600.),
                       ("use_temperature", True), ("temperature", 5900.)):
        light.set_editor_property(key, value)
    for name, position, lumens, radius in (("ReadingLight", (71, -169, 148), 400, 300),
                                          ("TaskLight", (239, 178, 109), 100, 150)):
        component = apartment.practical("RoomB_" + name, position, lumens, 2700, radius)
        room_b(component.get_owner())
    apartment.require(unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level(), "Could not save Room B")
    apartment.require(unreal.EditorAssetLibrary.save_directory(ART, only_if_is_dirty=True, recursive=True), "Could not save Room B assets")
    unreal.log("T05_ROOM_B_GENERATION_PASSED")


if __name__ == "__main__":
    build_room_b()
