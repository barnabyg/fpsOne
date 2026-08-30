"""Player-facing PIE automation for the reusable T02 Interaction seam."""

import unreal


MAP_ASSET = "/Game/Maps/L_Testbed"
PLAYER_ASSET = "/Game/Blueprints/BP_Player"
DOOR_ASSET = "/Game/Blueprints/BP_Door"
TEST_TARGET_ASSET = "/Game/Blueprints/BP_InteractionTestTarget"
INTERACTION_COMPONENT_ASSET = "/Game/Blueprints/BPC_Interaction"
INTERACTABLE_COMPONENT_ASSET = "/Game/Blueprints/BPC_Interactable"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def blueprint_class(asset_path):
    loaded_class = unreal.EditorAssetLibrary.load_blueprint_class(asset_path)
    require(loaded_class is not None, f"Could not load {asset_path}")
    return loaded_class


def property_value(instance, name):
    try:
        return instance.get_editor_property(name)
    except Exception:
        words = []
        current = ""
        for character in name:
            if character.isupper() and current:
                words.append(current)
                current = character.lower()
            else:
                current += character.lower()
        words.append(current)
        return instance.get_editor_property("_".join(words))


def wait_for(predicate, message, frames=240):
    for _ in range(frames):
        if predicate():
            return
        yield
    raise AssertionError(message)


def interaction_scenario():
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    require(level_subsystem.load_level(MAP_ASSET), "Could not load the T02 testbed map")

    player_class = blueprint_class(PLAYER_ASSET)
    door_class = blueprint_class(DOOR_ASSET)
    test_target_class = blueprint_class(TEST_TARGET_ASSET)
    interaction_class = blueprint_class(INTERACTION_COMPONENT_ASSET)
    interactable_class = blueprint_class(INTERACTABLE_COMPONENT_ASSET)

    level_subsystem.editor_request_begin_play()

    worlds = []
    yield from wait_for(
        lambda: bool(unreal.EditorLevelLibrary.get_pie_worlds(False)),
        "PIE world did not start",
    )
    worlds = unreal.EditorLevelLibrary.get_pie_worlds(False)
    world = worlds[0]

    yield from wait_for(
        lambda: len(unreal.GameplayStatics.get_all_actors_of_class(world, player_class)) == 1,
        "The Interaction test requires exactly one Player",
    )
    players = unreal.GameplayStatics.get_all_actors_of_class(world, player_class)
    doors = unreal.GameplayStatics.get_all_actors_of_class(world, door_class)
    test_targets = unreal.GameplayStatics.get_all_actors_of_class(world, test_target_class)
    require(len(players) == 1, "The Interaction test requires exactly one Player")
    require(len(doors) == 1, "The map must contain exactly one Door")
    require(len(test_targets) == 1, "The map must contain one nearby generic Interactable")

    player = players[0]
    primary_door = doors[0]
    interaction = player.get_component_by_class(interaction_class)
    interactable = primary_door.get_component_by_class(interactable_class)
    leaf = primary_door.get_component_by_class(unreal.StaticMeshComponent)
    require(interaction is not None, "Player does not own BPC_Interaction")
    require(interactable is not None, "Door does not supply the Interactable contract")
    require(leaf is not None, "Door has no collision leaf")

    controller = unreal.GameplayStatics.get_player_controller(world, 0)
    player.set_actor_location(unreal.Vector(-200.0, 0.0, 90.0), False, False)
    controller.set_control_rotation(unreal.Rotator())
    yield
    interaction.call_method("ScanForInteractionFocus")
    require(
        property_value(interaction, "CurrentFocus") == interactable,
        "An unobstructed Interactable inside 250 cm did not become Interaction Focus",
    )
    require(
        str(property_value(interaction, "CurrentPrompt")) == "E — Open",
        "Focused closed Door did not expose E — Open",
    )

    controller.set_control_rotation(unreal.Rotator(yaw=180.0))
    yield
    interaction.call_method("ScanForInteractionFocus")
    require(
        property_value(interaction, "CurrentFocus") is None,
        "Looking away did not clear Interaction Focus",
    )

    player.set_actor_location(unreal.Vector(-400.0, 0.0, 90.0), False, False)
    controller.set_control_rotation(unreal.Rotator())
    yield
    interaction.call_method("ScanForInteractionFocus")
    require(
        property_value(interaction, "CurrentFocus") is None,
        "An Interactable beyond 250 cm gained Interaction Focus",
    )

    occluders = unreal.GameplayStatics.get_all_actors_with_tag(
        world, unreal.Name("InteractionTestOccluder")
    )
    require(len(occluders) == 1, "The map must contain one Interaction occluder")
    occluder = occluders[0]
    player.set_actor_location(unreal.Vector(-200.0, 0.0, 90.0), False, False)
    occluder.set_actor_location(unreal.Vector(-100.0, 0.0, 140.0), False, False)
    yield
    interaction.call_method("ScanForInteractionFocus")
    require(
        property_value(interaction, "CurrentFocus") is None,
        "Occluding geometry did not block Interaction Focus",
    )

    occluder.set_actor_location(unreal.Vector(-100.0, 180.0, 140.0), False, False)
    yield
    interaction.call_method("ScanForInteractionFocus")
    require(
        property_value(interaction, "CurrentFocus") == interactable,
        "The direct Door did not remain the singular Interaction Focus",
    )

    player.set_actor_location(unreal.Vector(120.0, 0.0, 90.0), True, False)
    require(
        player.get_actor_location().x < 50.0,
        "The closed Door did not block passage",
    )
    player.set_actor_location(unreal.Vector(-200.0, 0.0, 90.0), False, False)
    yield
    interaction.call_method("ScanForInteractionFocus")

    interaction.call_method("TryInteract")
    yield
    require(
        leaf.get_collision_enabled() == unreal.CollisionEnabled.QUERY_ONLY,
        "Door leaf collision did not stop blocking passage while opening",
    )
    yield from wait_for(
        lambda: bool(property_value(primary_door, "IsOpen")),
        "Door did not complete its eased 0.75 second open transition",
    )

    player.set_actor_location(unreal.Vector(120.0, 0.0, 90.0), True, False)
    require(
        player.get_actor_location().x > 50.0,
        "The open Door did not permit passage into Room B",
    )
    controller.set_control_rotation(unreal.Rotator(yaw=180.0))
    yield
    interaction.call_method("ScanForInteractionFocus")
    require(
        str(property_value(interaction, "CurrentPrompt")) == "E — Close",
        "Focused open Door did not expose E — Close",
    )

    interaction.call_method("TryInteract")
    yield
    require(
        leaf.get_collision_enabled() == unreal.CollisionEnabled.QUERY_ONLY,
        "Door leaf collision blocked while closing",
    )
    yield from wait_for(
        lambda: not bool(property_value(primary_door, "IsOpen"))
        and leaf.get_collision_enabled() == unreal.CollisionEnabled.QUERY_AND_PHYSICS,
        "Door did not close and restore blocking collision",
    )

    unreal.log("T02_INTERACTION_FUNCTIONAL_TEST_PASSED")
    level_subsystem.editor_request_end_play()


unreal.AutomationScheduler.set_latent_command_timeout(60.0)
unreal.AutomationScheduler.add_latent_command(interaction_scenario())
