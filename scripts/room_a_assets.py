"""Import the pinned Room A sources and dress the 6 x 5 m living room.

Called in the isolated asset-regeneration project before publication. Gameplay
Blueprints are deliberately untouched; Door art follows its existing leaf.
"""

from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir()).resolve()
ART = "/Game/Environment/RoomA"
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MESHES = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
MATERIALS = unreal.MaterialEditingLibrary


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def import_file(source, destination, name=None):
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(source))
    task.set_editor_property("destination_path", destination)
    if name:
        task.set_editor_property("destination_name", name)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    objects = task.get_objects()
    require(objects, f"Import produced no assets: {source}")
    return objects


def model(identity, authored=False):
    source = (ROOT / "SourceArt/Authored" / (identity + ".glb") if authored else
              ROOT / "SourceArt/PolyHaven" / identity / (identity + "_2k.gltf"))
    destination = ART + "/" + identity
    if not unreal.EditorAssetLibrary.does_directory_exist(destination):
        import_file(source, destination)
    meshes = [unreal.load_asset(path) for path in unreal.EditorAssetLibrary.list_assets(destination)]
    meshes = [asset for asset in meshes if isinstance(asset, unreal.StaticMesh)]
    require(len(meshes) == (3 if identity == "potted_plant_02" else 1),
            f"Unexpected mesh count for {identity}: {len(meshes)}")
    for mesh in meshes:
        if "plant" not in identity:
            nanite = MESHES.get_nanite_settings(mesh)
            nanite.set_editor_property("enabled", True)
            MESHES.set_nanite_settings(mesh, nanite)
        if MESHES.get_simple_collision_count(mesh) == 0:
            MESHES.add_simple_collisions(mesh, unreal.ScriptCollisionShapeType.BOX)
        unreal.log(f"ROOM_A_MESH {identity}/{mesh.get_name()}: {mesh.get_bounding_box()}")
    # Interchange bBakeMeshes (the pinned default) bakes node transforms into
    # each mesh. Keep the plant parts together without adding duplicate sources.
    return meshes if len(meshes) > 1 else meshes[0]


def expression(material, kind, **properties):
    node = MATERIALS.create_material_expression(material, kind)
    for key, value in properties.items():
        node.set_editor_property(key, value)
    return node


def color_material(name, color, roughness=0.6, metallic=0.0, emission=0.0):
    path = ART + "/Materials/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        material = unreal.load_asset(path)
        MATERIALS.set_material_usage(material, unreal.MaterialUsage.MATUSAGE_NANITE)
        return material
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, ART + "/Materials", unreal.Material, unreal.MaterialFactoryNew())
    color_node = expression(material, unreal.MaterialExpressionConstant3Vector,
                            constant=unreal.LinearColor(*color, 1))
    MATERIALS.connect_material_property(color_node, "", unreal.MaterialProperty.MP_BASE_COLOR)
    for prop, value in ((unreal.MaterialProperty.MP_ROUGHNESS, roughness),
                        (unreal.MaterialProperty.MP_METALLIC, metallic)):
        node = expression(material, unreal.MaterialExpressionConstant, r=value)
        MATERIALS.connect_material_property(node, "", prop)
    if emission:
        glow = expression(material, unreal.MaterialExpressionConstant3Vector,
                          constant=unreal.LinearColor(*(c * emission for c in color), 1))
        MATERIALS.connect_material_property(glow, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MATERIALS.recompile_material(material)
    MATERIALS.set_material_usage(material, unreal.MaterialUsage.MATUSAGE_NANITE)
    return material


def pbr_material(name, identity, tint=None, uv=(1.0, 1.0), subtle_color=False):
    material = color_material(name, (1, 1, 1))
    MATERIALS.delete_all_material_expressions(material)
    coords = expression(material, unreal.MaterialExpressionTextureCoordinate, u_tiling=uv[0], v_tiling=uv[1])
    for channel, prop in (("diff", unreal.MaterialProperty.MP_BASE_COLOR),
                          ("nor_dx", unreal.MaterialProperty.MP_NORMAL),
                          ("rough", unreal.MaterialProperty.MP_ROUGHNESS)):
        pattern = "*col_1*" if identity == "fabric_pattern_07" and channel == "diff" else "*" + channel + "*"
        source = list((ROOT / "SourceArt/PolyHaven" / identity).glob(pattern + ".jpg"))[0]
        texture_path = ART + "/Textures/" + source.stem
        if not unreal.EditorAssetLibrary.does_asset_exist(texture_path):
            import_file(source, ART + "/Textures")
        texture = unreal.load_asset(texture_path)
        texture.set_editor_property("srgb", channel == "diff")
        if channel == "nor_dx":
            texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        elif channel == "rough":
            texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
        sample = expression(material, unreal.MaterialExpressionTextureSample, texture=texture)
        if channel == "nor_dx":
            sample.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        elif channel == "rough":
            sample.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
        MATERIALS.connect_material_expressions(coords, "", sample, "UVs")
        output = sample
        if channel == "diff" and tint:
            if subtle_color:
                # Keep the source's fine surface variation without its plaid
                # colour or aged plaster staining in the apartment palette.
                variation = expression(material, unreal.MaterialExpressionMultiply, const_b=0.12)
                MATERIALS.connect_material_expressions(sample, "R", variation, "A")
                base = expression(material, unreal.MaterialExpressionAdd, const_b=0.88)
                MATERIALS.connect_material_expressions(variation, "", base, "A")
                output = base
            multiply = expression(material, unreal.MaterialExpressionMultiply)
            color = expression(material, unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(*tint, 1))
            MATERIALS.connect_material_expressions(output, "", multiply, "A")
            MATERIALS.connect_material_expressions(color, "", multiply, "B")
            output = multiply
        MATERIALS.connect_material_property(output, "", prop)
    MATERIALS.recompile_material(material)
    return material


def actor(kind, name, location, rotation=(0, 0, 0)):
    result = ACTORS.spawn_actor_from_class(kind, unreal.Vector(*location),
                                          unreal.Rotator(pitch=rotation[0], yaw=rotation[1], roll=rotation[2]))
    require(result, f"Could not spawn {name}")
    result.set_actor_label(name)
    result.set_editor_property("tags", [unreal.Name("RoomAArt")])
    return result


def mesh_actor(name, mesh, location, scale=(1, 1, 1), yaw=0, material=None, collision=True):
    if isinstance(mesh, list):
        return [mesh_actor(name + "_" + part.get_name(), part, location, scale, yaw,
                           material, collision and part.get_name().endswith("_pot")) for part in mesh]
    result = actor(unreal.StaticMeshActor, name, location, (0, yaw, 0))
    result.set_actor_scale3d(unreal.Vector(*scale))
    component = result.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_mobility(unreal.ComponentMobility.STATIC)
    component.set_collision_profile_name("BlockAll" if collision else "NoCollision")
    if material:
        component.set_material(0, material)
    return result


def box(name, location, size, material, collision=True):
    return mesh_actor(name, unreal.load_asset("/Engine/BasicShapes/Cube"), location,
                      tuple(d / 100 for d in size), material=material, collision=collision)


def practical(name, location, intensity, temperature, radius=350):
    light = actor(unreal.PointLight, name, location).point_light_component
    light.set_mobility(unreal.ComponentMobility.MOVABLE)
    light.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
    light.set_editor_property("intensity", intensity)
    light.set_editor_property("use_temperature", True)
    light.set_editor_property("temperature", temperature)
    light.set_editor_property("attenuation_radius", radius)
    light.set_editor_property("source_radius", 6.0)
    return light


def build_room_a():
    materials = {
        "Oak": pbr_material("M_Oak", "wood_floor"),
        "Linen": pbr_material("M_Linen", "fabric_pattern_07", (0.46, 0.42, 0.34), (12, 12), True),
        "Rug": pbr_material("M_Rug", "fabric_pattern_07", (0.13, 0.20, 0.18), (12, 12), True),
        "Piping": color_material("M_Piping", (0.22, 0.20, 0.16), 0.95),
        "Bronze": color_material("M_Bronze", (0.075, 0.060, 0.040), 0.3, 0.8),
        "Shade": color_material("M_Shade", (0.72, 0.62, 0.44), 0.9, emission=0.6),
    }
    floor = pbr_material("M_Floor", "wood_floor", uv=(3, 2.5))
    wall = pbr_material("M_WarmPlaster", "white_plaster_02", (0.60, 0.55, 0.46), (3, 2), True)
    ceiling = color_material("M_Ceiling", (0.70, 0.68, 0.61), 0.95)
    trim = color_material("M_Trim", (0.58, 0.55, 0.47), 0.42)
    accent = color_material("M_SagePaint", (0.14, 0.19, 0.17), 0.83)
    dark = color_material("M_Charcoal", (0.018, 0.023, 0.022), 0.55)
    paper = color_material("M_Paper", (0.72, 0.67, 0.53), 0.85)
    ochre = color_material("M_Ochre", (0.40, 0.16, 0.045), 0.8)
    art_white = color_material("M_ArtPaper", (0.68, 0.61, 0.47), 0.9)

    imported = {identity: model(identity) for identity in
                ("modern_arm_chair_01", "modern_coffee_table_01", "potted_plant_02", "ceramic_vase_03")}
    authored = {identity: model(identity, True) for identity in
                ("SM_LinenSofa", "SM_Sideboard", "SM_FloorLamp", "SM_Rug")}
    for mesh in authored.values():
        for index, slot in enumerate(mesh.get_editor_property("static_materials")):
            name = str(slot.material_slot_name)
            require(name in materials, f"Unknown authored material slot: {name}")
            mesh.set_material(index, materials[name])

    require(unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level("/Game/Maps/L_Testbed"), "Map not found")
    existing = {item.get_actor_label(): item for item in ACTORS.get_all_level_actors()}
    for item in list(existing.values()):
        if item.actor_has_tag("RoomAArt") or item.get_actor_label() in (
                "RoomA_SouthWall", "InteractionDistractor", "InteractionTestOccluder",
                "SkyLight_T02", "DirectionalLight_T02", "PointLight_T02"):
            ACTORS.destroy_actor(item)
    for label, material in (("RoomA_Floor", floor), ("RoomA_Ceiling", ceiling),
                            ("RoomA_NorthWall", accent), ("RoomA_WestWall", wall),
                            ("SharedWall_North", wall), ("SharedWall_South", wall)):
        existing[label].static_mesh_component.set_material(0, material)

    # Clear internal footprint is 600 x 500 cm, with finished floor at z=0 and
    # ceiling underside z=270. Wall thickness grows outward, not into the Room.
    existing["RoomA_NorthWall"].set_actor_location(unreal.Vector(-300, 260, 135), False, False)
    existing["RoomA_WestWall"].set_actor_location(unreal.Vector(-610, 0, 135), False, False)
    existing["RoomA_Ceiling"].set_actor_scale3d(unreal.Vector(6.2, 5.4, 0.2))
    for label, y in (("SharedWall_North", 150), ("SharedWall_South", -150)):
        existing[label].set_actor_location(unreal.Vector(10, y, 135), False, False)
    # Hide Room B's wall ends inside the shared partition, avoiding coplanar
    # blockout faces showing through the finished plaster from Room A.
    for label, y in (("RoomB_NorthWall", 200), ("RoomB_SouthWall", -200)):
        existing[label].set_actor_location(unreal.Vector(205, y, 135), False, False)
        existing[label].set_actor_scale3d(unreal.Vector(3.9, 0.2, 2.7))
    box("WindowWall_West", (-545, -260, 135), (110, 20, 270), wall)
    box("WindowWall_East", (-90, -260, 135), (180, 20, 270), wall)
    box("WindowWall_Sill", (-335, -260, 40), (310, 20, 80), wall)
    box("WindowWall_Head", (-335, -260, 256), (310, 20, 28), wall)
    box("Window_Sill", (-335, -246, 81), (318, 34, 4), trim)
    for x in (-490, -180, -387, -283):
        box("Window_Mullion", (x, -253, 161), (5, 9, 162), dark)
    for z in (83, 240):
        box("Window_Rail", (-335, -253, z), (315, 9, 5), dark)
    # A nearby, inaccessible courtyard parapet avoids an unfinished black void
    # below the atmospheric horizon while keeping the upper glazing open to sky.
    box("Courtyard_Parapet", (-335, -420, 90), (1100, 20, 180), wall)
    box("Courtyard_Coping", (-335, -420, 182), (1120, 27, 6), trim)
    # A blocked opening admits daylight but remains an inaccessible exterior.
    barrier = box("Window_InvisibleBarrier", (-335, -264, 161), (310, 2, 160), dark)
    barrier.set_actor_hidden_in_game(True)
    barrier.static_mesh_component.set_cast_shadow(False)
    for x, size in ((-550, 100), (-85, 170)):
        box("South_Skirting", (x, -248, 5), (size, 2.5, 10), trim)
    box("UnderWindow_Skirting", (-335, -248, 5), (310, 2.5, 10), trim)
    box("North_Skirting", (-300, 248, 5), (600, 2.5, 10), trim)
    box("West_Skirting", (-598, 0, 5), (2.5, 500, 10), trim)
    for y in (-155, 155):
        box("Shared_Skirting", (-1.25, y, 5), (2.5, 190, 10), trim)
    box("Door_Overwall", (10, 0, 243), (20, 100, 54), wall)
    for y in (-55, 55):
        box("Door_Casing", (-4, y, 108), (5, 9, 216), trim, False)
    box("Door_CasingHead", (-4, 0, 216), (5, 119, 9), trim, False)
    door_leaf = existing["Door"].get_component_by_class(unreal.StaticMeshComponent)
    door_leaf.set_material(0, materials["Oak"])
    # Fixed detailing is attached to the moving leaf; all collision remains on
    # the original leaf so its tested open/close behavior is unchanged.
    for y in (-38, 38):
        panel = box("Door_Inlay", (-6.2, y, 108), (0.6, 1.2, 172), materials["Bronze"], False)
        panel.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        panel.attach_to_component(door_leaf, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
    handle = box("Door_Handle", (-10, -32, 102), (8, 14, 2), materials["Bronze"], False)
    handle.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    handle.attach_to_component(door_leaf, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)

    mesh_actor("LinenSofa", authored["SM_LinenSofa"], (-393, 195, 0), yaw=180)
    mesh_actor("WovenRug", authored["SM_Rug"], (-360, 56, 0), collision=False)
    mesh_actor("CoffeeTable", imported["modern_coffee_table_01"], (-326, 54, 0), yaw=90)
    mesh_actor("LoungeChair", imported["modern_arm_chair_01"], (-145, 125, 0), yaw=110)
    mesh_actor("Sideboard", authored["SM_Sideboard"], (-390, -225, 0))
    mesh_actor("FloorLamp", authored["SM_FloorLamp"], (-213, 201, 0))
    practical("FloorLamp_WarmBulb", (-213, 201, 148), 450, 2700, 340)
    mesh_actor("WindowPlant", imported["potted_plant_02"], (-193, -208, 0))
    mesh_actor("CabinetVase", imported["ceramic_vase_03"], (-437, -225, 68), (0.85, 0.85, 0.85), collision=False)
    mesh_actor("TableVase", imported["ceramic_vase_03"], (-340, 52, 39), (0.46, 0.46, 0.46), collision=False)
    for i, color in enumerate((dark, ochre, accent)):
        box("CoffeeTable_Book", (-295, 50 + i, 40 + i * 2.2), (23, 17, 2), color, False)
        box("CoffeeTable_Pages", (-295, 49.5 + i, 40.1 + i * 2.2), (22, 16.7, 1.3), paper, False)
    for i in range(7):
        box("Cabinet_Book", (-369 + i * 4, -225, 77), (3.6, 17, 18 + i % 3 * 2), (dark, ochre, accent)[i % 3], False)
    # Project-authored geometric diptych, framed and inset against the sage wall.
    for x, reverse in ((-430, False), (-347, True)):
        box("Art_Frame", (x, 245, 173), (66, 4, 83), materials["Oak"], False)
        box("Art_Mat", (x, 242.7, 173), (61, 0.8, 78), art_white, False)
        box("Art_ColourField", (x + (6 if reverse else -6), 242.1, 166), (34, 0.3, 46), ochre if reverse else accent, False)
        circle = mesh_actor("Art_Circle", unreal.load_asset("/Engine/BasicShapes/Cylinder"),
                            (x, 241.7, 188), (0.30, 0.30, 0.003), material=dark, collision=False)
        circle.set_actor_rotation(unreal.Rotator(roll=90), False)
    # Restrained wall fixture gives the Door end of the Room a warm reference.
    box("WallSconce_Back", (-3, 160, 177), (5, 13, 24), materials["Bronze"], False)
    box("WallSconce_Diffuser", (-7, 160, 177), (5, 9, 18), materials["Shade"], False)
    practical("WallSconce_WarmBulb", (-16, 160, 178), 160, 2700, 230)

    player_start = next(item for item in existing.values() if isinstance(item, unreal.PlayerStart))
    player_start.set_actor_location(unreal.Vector(-550, -120, 90), False, False)
    player_start.set_actor_rotation(unreal.Rotator(pitch=-6, yaw=23), False)
    player_start.set_actor_label("PlayerStart_RoomA")
    existing["NPC_A"].set_actor_location(unreal.Vector(-260, -180, 90), False, False)

    actor(unreal.SkyAtmosphere, "AfternoonSky", (0, 0, 0))
    sun = actor(unreal.DirectionalLight, "AfternoonSun", (0, -400, 500), (-23, 70, 0)).get_component_by_class(unreal.DirectionalLightComponent)
    sun.set_mobility(unreal.ComponentMobility.MOVABLE)
    sun.set_editor_property("atmosphere_sun_light", True)
    sun.set_editor_property("intensity", 6000.0)
    sun.set_editor_property("use_temperature", True)
    sun.set_editor_property("temperature", 4400.0)
    sun.set_editor_property("light_source_angle", 1.8)
    skylight = actor(unreal.SkyLight, "AfternoonSkyLight", (0, 0, 300)).get_component_by_class(unreal.SkyLightComponent)
    skylight.set_mobility(unreal.ComponentMobility.MOVABLE)
    skylight.set_editor_property("real_time_capture", True)
    skylight.set_editor_property("intensity", 0.7)
    fill = actor(unreal.RectLight, "Window_SoftDaylight", (-335, -241, 180), (0, 90, 0)).get_component_by_class(unreal.RectLightComponent)
    fill.set_mobility(unreal.ComponentMobility.MOVABLE)
    fill.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
    fill.set_editor_property("intensity", 2400.0)
    fill.set_editor_property("source_width", 290.0)
    fill.set_editor_property("source_height", 140.0)
    fill.set_editor_property("attenuation_radius", 750.0)
    fill.set_editor_property("use_temperature", True)
    fill.set_editor_property("temperature", 6200.0)
    practical("RoomB_BlockoutLight", (200, 0, 235), 900, 4200, 400)
    volume = actor(unreal.PostProcessVolume, "RoomA_Exposure", (0, 0, 0))
    volume.set_editor_property("unbound", True)
    settings = volume.get_editor_property("settings")
    for name, value in (("auto_exposure_min_brightness", 7.5), ("auto_exposure_max_brightness", 7.5),
                        ("auto_exposure_bias", -3.0),
                        ("bloom_intensity", 0.15), ("motion_blur_amount", 0.0)):
        settings.set_editor_property("override_" + name, True)
        settings.set_editor_property(name, value)
    volume.set_editor_property("settings", settings)
    require(unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level(), "Could not save furnished Room A")
    require(unreal.EditorAssetLibrary.save_directory(ART, only_if_is_dirty=True, recursive=True), "Could not save Room A assets")
    unreal.log("T04_ROOM_A_GENERATION_PASSED")


if __name__ == "__main__":
    build_room_a()
