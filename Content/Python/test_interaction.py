"""Player-facing PIE automation for the reusable T02 Interaction seam."""

import math
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


def exercise_door_motion(world, controller, leaf, closed_location, interaction, interactable, opening):
    """Inject E through PlayerInput and observe motion, not private Door state."""
    start = unreal.GameplayStatics.get_time_seconds(world)
    samples = []
    unreal.SystemLibrary.execute_console_command(world, "Input.+key E", controller)
    try:
        for frame in range(240):
            yield
            elapsed = unreal.GameplayStatics.get_time_seconds(world) - start
            angle = leaf.get_world_rotation().yaw
            progress = angle / 90.0 if opening else 1.0 - angle / 90.0
            radians = math.radians(angle)
            expected_midpoint = closed_location + unreal.Vector(
                50.0 * math.sin(radians), 50.0 * (1.0 - math.cos(radians)), 0.0
            )
            require(
                (leaf.get_world_location() - expected_midpoint).length() < 1.0,
                "Visible Door leaf did not follow its inward swing arc",
            )
            samples.append((elapsed, progress))
            if frame == 1:
                unreal.SystemLibrary.execute_console_command(world, "Input.-key E", controller)
            require(-0.001 <= progress <= 1.001, "Door motion overshot its 90 degree arc")
            if 0.05 < elapsed < 0.65:
                require(
                    leaf.get_collision_enabled() == unreal.CollisionEnabled.QUERY_ONLY,
                    "Door leaf blocked passage during its transition",
                )
                require(
                    not bool(property_value(interactable, "InteractionAvailable")),
                    "Door remained available while moving",
                )
                require(
                    property_value(interaction, "CurrentFocus") is None
                    and str(property_value(interaction, "CurrentPrompt")) == "",
                    "Player Tick did not clear unavailable focus and prompt",
                )
            if progress >= 0.9999:
                break
            require(elapsed < 1.0, "The bound E key did not complete the Door transition")
        else:
            raise AssertionError("Door transition exceeded the frame limit")
    finally:
        unreal.SystemLibrary.execute_console_command(world, "Input.-key E", controller)

    require(0.72 <= elapsed <= 0.85, f"Door transition was not 0.75 seconds: {elapsed}")
    quarter = min(samples, key=lambda sample: abs(sample[0] - 0.1875))[1]
    middle = min(samples, key=lambda sample: abs(sample[0] - 0.375))[1]
    late = min(samples, key=lambda sample: abs(sample[0] - 0.5625))[1]
    require(0.05 < quarter < 0.20, f"Door did not ease in: quarter progress {quarter}")
    require(0.40 < middle < 0.60, f"Door midpoint was incorrect: {middle}")
    require(0.80 < late < 0.96, f"Door did not ease out: three-quarter progress {late}")
    yield
    expected_collision = (
        unreal.CollisionEnabled.QUERY_ONLY if opening
        else unreal.CollisionEnabled.QUERY_AND_PHYSICS
    )
    require(leaf.get_collision_enabled() == expected_collision, "Door final collision state was incorrect")
    require(bool(property_value(interactable, "InteractionAvailable")), "Door did not restore Interaction availability")


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
    closed_leaf_location = leaf.get_world_location()
    require(
        abs(closed_leaf_location.x) < 1.0 and abs(closed_leaf_location.y) < 1.0,
        "Closed Door leaf is not centred in the shared opening",
    )

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

    generic = test_targets[0].get_component_by_class(interactable_class)
    player.set_actor_location(unreal.Vector(-200.0, 130.0, 90.0), False, False)
    controller.set_control_rotation(unreal.Rotator(pitch=-17.0))
    yield
    yield
    interaction.call_method("ScanForInteractionFocus")
    require(property_value(interaction, "CurrentFocus") == generic, "The generic Interactable could not gain focus")
    require(
        str(property_value(interaction, "CurrentPrompt")) == "E — Interact",
        "The generic Interactable did not supply its own prompt",
    )
    player.set_actor_location(unreal.Vector(-200.0, 0.0, 90.0), False, False)
    controller.set_control_rotation(unreal.Rotator())
    yield
    yield

    player.set_actor_location(unreal.Vector(120.0, 0.0, 90.0), True, False)
    require(
        player.get_actor_location().x < 50.0,
        "The closed Door did not block passage",
    )
    player.set_actor_location(unreal.Vector(-200.0, 0.0, 90.0), False, False)
    yield
    interaction.call_method("ScanForInteractionFocus")

    yield from exercise_door_motion(
        world, controller, leaf, closed_leaf_location, interaction, interactable, opening=True
    )
    open_leaf_location = leaf.get_world_location()
    leaf_rotation = leaf.get_world_rotation()
    require(
        abs(leaf_rotation.yaw - 90.0) < 1.0,
        f"Door leaf did not complete its 90 degree opening rotation: {leaf_rotation}",
    )
    require(
        open_leaf_location.x > 49.0 and open_leaf_location.y > 49.0,
        "Door leaf did not swing wholly inward into Room B",
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

    yield from exercise_door_motion(
        world, controller, leaf, closed_leaf_location, interaction, interactable, opening=False
    )
    require(
        (leaf.get_world_location() - closed_leaf_location).length() < 1.0,
        "Door did not return to its original closed transform",
    )
    player.set_actor_location(unreal.Vector(-200.0, 0.0, 90.0), True, False)
    require(player.get_actor_location().x > 0.0, "Closed Door did not restore its passage obstruction")

    unreal.log("T02_INTERACTION_FUNCTIONAL_TEST_PASSED")
    level_subsystem.editor_request_end_play()


unreal.AutomationScheduler.set_latent_command_timeout(60.0)
unreal.AutomationScheduler.add_latent_command(interaction_scenario())
