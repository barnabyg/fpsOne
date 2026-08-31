"""Player-facing PIE automation for the reusable T02 Interaction seam."""

import math
import os
import hashlib
import json
import struct
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


def press_e(world, controller):
    unreal.SystemLibrary.execute_console_command(world, "Input.+key E", controller)
    yield
    unreal.SystemLibrary.execute_console_command(world, "Input.-key E", controller)
    yield
    yield


def hold_input(world, controller, key, frames, value=1.0):
    unreal.SystemLibrary.execute_console_command(world, f"Input.+key {key} {value}", controller)
    try:
        for _ in range(frames):
            yield
    finally:
        unreal.SystemLibrary.execute_console_command(world, f"Input.-key {key}", controller)
    yield
    yield


def capture_presentation(world, controller, name):
    """Optional rendered evidence; the normal functional run remains headless."""
    if "-T03Capture" not in unreal.SystemLibrary.get_command_line():
        return
    require(unreal.SystemLibrary.get_console_variable_int_value("r.MotionVectorSimulation") == 0,
            "The TSR warning exception requires disabled, unchanged motion-vector simulation")
    root = os.path.join(unreal.Paths.project_saved_dir(), "DialogueReview")
    os.makedirs(root, exist_ok=True)
    filename = os.path.abspath(os.path.join(root, name + ".png"))
    if os.path.exists(filename):
        os.remove(filename)
    for _ in range(120):
        yield
    pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
    unreal.log(f"T04_UI_CAMERA {name}: {controller.get_control_rotation()} / {pawn.get_actor_location()}")
    unreal.SystemLibrary.execute_console_command(world, f'Shot -nosuffix filename="{filename}"', controller)
    yield from wait_for(lambda: os.path.exists(filename), f"Presentation capture did not arrive: {filename}")


def capture_room(world, controller, name="room-a-overview", folder="RoomAReview", flag="-T04Capture"):
    if flag not in unreal.SystemLibrary.get_command_line():
        return
    root = os.path.abspath(os.path.join(unreal.Paths.project_saved_dir(), folder))
    os.makedirs(root, exist_ok=True)
    filename = os.path.join(root, name + ".png")
    if os.path.exists(filename):
        os.remove(filename)
    for _ in range(120):
        yield
    unreal.log(f"T04_CAMERA: {controller.get_control_rotation()} / {unreal.GameplayStatics.get_player_pawn(world, 0).get_actor_location()}")
    unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 32", controller)
    unreal.SystemLibrary.execute_console_command(world, f'HighResShot 2560x1440 filename="{filename}"', controller)
    yield from wait_for(lambda: os.path.exists(filename), f"Acceptance screenshot did not arrive: {name}")
    for _ in range(5):
        yield
    with open(filename, "rb") as stream:
        data = stream.read()
    width, height = struct.unpack(">II", data[16:24])
    require((width, height) == (2560, 1440), "Room acceptance must capture at 2560 x 1440")
    pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
    location, rotation = pawn.get_actor_location(), controller.get_control_rotation()
    metadata = dict(screenshot=name + ".png", sha256=hashlib.sha256(data).hexdigest(),
                    width=width, height=height,
                    playerLocation=[location.x, location.y, location.z],
                    viewRotation=[rotation.pitch, rotation.yaw, rotation.roll],
                    frameSeconds=unreal.GameplayStatics.get_world_delta_seconds(world),
                    engine=unreal.SystemLibrary.get_engine_version())
    with open(os.path.join(root, "capture.json"), "w", encoding="utf-8") as stream:
        json.dump(metadata, stream, indent=2)
    unreal.log("T04_ROOM_A_CAPTURE_PASSED" if flag == "-T04Capture" else f"T05_CAPTURE_PASSED {name}")


def add_test_fixtures(test_target_class):
    """Unsaved editor setup; test props never ship in the furnished apartment."""
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    target = subsystem.spawn_actor_from_class(test_target_class, unreal.Vector(-40, -80, 105), unreal.Rotator(yaw=90))
    target.set_actor_hidden_in_game(True)
    occluder = subsystem.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(-100, 180, 140), unreal.Rotator())
    occluder.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube"))
    occluder.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    occluder.set_actor_scale3d(unreal.Vector(0.2, 0.8, 2.8))
    occluder.set_editor_property("tags", [unreal.Name("InteractionTestOccluder")])
    occluder.set_actor_hidden_in_game(True)


def exercise_both_dialogues(world, player, controller, interactable_class, cycles=3):
    npcs = sorted(unreal.GameplayStatics.get_all_actors_with_tag(world, unreal.Name("DialogueNPC")), key=lambda actor: actor.get_actor_location().x)
    expected_exchanges = (
        ("Resident A: The light is warm in here this afternoon.", "Player: It is a quiet place to take a break.", "Resident A: You are welcome to look around."),
        ("Resident B: I have just finished tidying the desk.", "Player: The room looks ready for the evening.", "Resident B: Yes, there is nothing else to do for now."),
    )
    presentation = controller.get_hud()
    require(len(npcs) == 2, "Both dialogue occupants must exist on launch")
    for index, npc in enumerate(npcs):
        require(npc.get_component_by_class(interactable_class) is not None, "NPC must supply the shared Interactable contract")
        direction = 1.0 if index == 0 else -1.0
        start = npc.get_actor_location() + unreal.Vector(direction * 150.0, 0.0, 0.0)
        player.set_actor_location(start, False, False)
        controller.set_control_rotation(unreal.Rotator(yaw=180.0 if index == 0 else 0.0))
        yield
        player.set_actor_location(npc.get_actor_location() - unreal.Vector(direction * 100.0, 0.0, 0.0), True, False)
        require((player.get_actor_location().x - npc.get_actor_location().x) * direction > 50.0, "The NPC capsule must block the Player")
        player.set_actor_location(start, False, False)
        yield
        yield
        for _ in range(cycles):
            require(str(property_value(presentation, "PromptText")) == "E — Talk", "Either NPC must present the shared Talk prompt")
            for expected in expected_exchanges[index]:
                yield from press_e(world, controller)
                require(bool(property_value(presentation, "DialogueVisible")), "The shared dialogue panel must be visible")
                require(str(property_value(presentation, "DialogueText")) == expected, "Either NPC must replay its own speaker-labelled lines in order")
            yield from press_e(world, controller)
            require(not bool(property_value(presentation, "DialogueVisible")), "Either exchange must dismiss after its last line")
            require(controller.get_hud() == presentation, "Both NPCs must reuse the same presentation")


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

    add_test_fixtures(test_target_class)

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
    yield
    yield
    require(str(property_value(controller.get_hud(), "PromptText")) == "",
            "Room A spawn must not initially focus the Door or NPC A")
    yield from capture_room(world, controller)
    # Sweep the real Player capsule through the circulation aisle; furnishings
    # must leave a usable approach to the shared Door from the accepted spawn.
    for destination in (unreal.Vector(-550, -70, 90), unreal.Vector(-170, -70, 90), unreal.Vector(-170, 0, 90)):
        player.set_actor_location(destination, True, False)
        require((player.get_actor_location() - destination).length() < 5,
                f"Room A furnishings obstruct the Player's route from spawn to the Door: wanted {destination}, got {player.get_actor_location()}")
    test_targets[0].set_actor_hidden_in_game(False)
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
    occluder.set_actor_hidden_in_game(False)
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
    player.set_actor_location(unreal.Vector(-200.0, -80.0, 90.0), False, False)
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
    # Capture only the shipped environment, hiding unsaved test fixtures.
    test_targets[0].set_actor_hidden_in_game(True)
    occluder.set_actor_hidden_in_game(True)
    player.set_actor_location(unreal.Vector(-170, -55, 90), False, False)
    controller.set_control_rotation(unreal.Rotator(pitch=-6, yaw=15))
    yield from capture_room(world, controller, "open-door-transition", "DoorReview", "-T05Capture")
    player.set_actor_location(unreal.Vector(65, 15, 90), False, False)
    controller.set_control_rotation(unreal.Rotator(pitch=-12, yaw=-8))
    yield from capture_room(world, controller, "room-b-overview", "RoomBReview", "-T05Capture")
    player.set_actor_location(unreal.Vector(-200, 0, 90), False, False)
    controller.set_control_rotation(unreal.Rotator())

    player.set_actor_location(unreal.Vector(120.0, 0.0, 90.0), True, False)
    require(
        player.get_actor_location().x > 50.0,
        "The open Door did not permit passage into Room B",
    )
    # T05: observe the furnished space using the real Player capsule, without
    # coupling acceptance to actor names or the furniture's implementation.
    for destination in (unreal.Vector(200, 0, 90), unreal.Vector(200, -70, 90),
                        unreal.Vector(80, -70, 90), unreal.Vector(80, 100, 90),
                        unreal.Vector(120, 0, 90)):
        player.set_actor_location(destination, True, False)
        require((player.get_actor_location() - destination).length() < 5,
                f"Room B furnishings obstruct circulation: {destination}")
    player.set_actor_location(unreal.Vector(200, -70, 90), False, False)
    player.set_actor_location(unreal.Vector(200, -180, 90), True, False)
    require(player.get_actor_location().y > -145,
            "Room B guest bed must block the Player")
    # Check the window above the sill so the wall below cannot mask a missing
    # barrier; this prevents an unintended accessible exterior.
    player.set_actor_location(unreal.Vector(300, 0, 175), False, False)
    player.set_actor_location(unreal.Vector(500, 0, 175), True, False)
    require(player.get_actor_location().x < 420,
            "Room B window must block access outside the two Rooms")
    player.set_actor_location(unreal.Vector(120, 0, 90), False, False)
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

    npcs = unreal.GameplayStatics.get_all_actors_with_tag(world, unreal.Name("DialogueNPC"))
    require(len(npcs) == 2, "Each Room must contain one proxy Dialogue NPC")
    require(
        sum(npc.get_actor_location().x < 0.0 for npc in npcs) == 1,
        "Proxy NPCs must occupy different Rooms",
    )
    npc = min(npcs, key=lambda actor: actor.get_actor_location().x)
    player.set_actor_location(npc.get_actor_location() + unreal.Vector(150.0, 0.0, 0.0), False, False)
    controller.set_control_rotation(unreal.Rotator(yaw=180.0))
    yield
    yield
    require(str(property_value(interaction, "CurrentPrompt")) == "E — Talk", "Focused NPC must offer E — Talk")
    yield from press_e(world, controller)
    presentation = controller.get_hud()
    require(bool(property_value(presentation, "DialogueVisible")), "E must open the dialogue panel")
    require(str(property_value(presentation, "DialogueText")) == "Resident A: The light is warm in here this afternoon.", f"E must present NPC A's initial speaker-labelled line; got {property_value(presentation, 'DialogueText')}")
    yield from capture_presentation(world, controller, "npc-a-dialogue")
    yield from press_e(world, controller)
    require(str(property_value(presentation, "DialogueText")) == "Player: It is a quiet place to take a break.", "E must advance exactly one dialogue line")
    yield from press_e(world, controller)
    require(str(property_value(presentation, "DialogueText")) == "Resident A: You are welcome to look around.", "The final line must remain visible until E")
    yield from press_e(world, controller)
    require(not bool(property_value(presentation, "DialogueVisible")), "E after the final line must dismiss dialogue")
    yield from press_e(world, controller)
    require(str(property_value(presentation, "DialogueText")) == "Resident A: The light is warm in here this afternoon.", "A replay must start from the first line")
    require(property_value(interaction, "CurrentFocus") is None, "Dialogue must suspend Interaction scanning")
    require(str(property_value(presentation, "PromptText")) == "", "Dialogue must hide the Interaction Prompt")
    stationary = player.get_actor_location()
    for key in ("W", "S", "A", "D"):
        yield from hold_input(world, controller, key, 12)
        require((player.get_actor_location() - stationary).length() < 1.0, f"{key} moved the Player during dialogue")
    starting_view = controller.get_control_rotation()
    yield from hold_input(world, controller, "MouseX", 20, 20.0)
    yaw_change = (controller.get_control_rotation().yaw - starting_view.yaw + 180) % 360 - 180
    require(2.0 < abs(yaw_change) <= 35.1, f"Dialogue mouse look must remain available but bounded: {yaw_change}")
    yield from hold_input(world, controller, "MouseY", 20, 20.0)
    pitch_change = (controller.get_control_rotation().pitch - starting_view.pitch + 180) % 360 - 180
    require(2.0 < abs(pitch_change) <= 20.1, f"Dialogue pitch must remain available but bounded: {pitch_change}")
    require(property_value(interaction, "CurrentFocus") is None, "Mouse look must not resume Interaction scanning")
    for _ in range(3):
        yield from press_e(world, controller)
    require(not bool(property_value(presentation, "DialogueVisible")), "Dialogue completion must restore exploration presentation")
    controller.set_control_rotation(unreal.Rotator(yaw=180.0))
    yield
    yield
    require(str(property_value(presentation, "PromptText")) == "E — Talk", "Dismissal must restore scanning and the Talk prompt")
    yield from capture_presentation(world, controller, "npc-a-restored")
    yield from hold_input(world, controller, "S", 12)
    require((player.get_actor_location() - stationary).length() > 5.0, "Dismissal must restore walking input")
    yaw_before = controller.get_control_rotation().yaw
    yield from hold_input(world, controller, "MouseX", 20, 20.0)
    yaw_change = (controller.get_control_rotation().yaw - yaw_before + 180) % 360 - 180
    require(abs(yaw_change) > 40.0, "Dismissal must restore unrestricted yaw")
    yield from exercise_both_dialogues(world, player, controller, interactable_class)

    # Leave both kinds of Interaction changed before starting a fresh session.
    player.set_actor_location(unreal.Vector(120.0, 0.0, 90.0), False, False)
    controller.set_control_rotation(unreal.Rotator(yaw=180.0))
    yield
    yield
    yield from exercise_door_motion(world, controller, leaf, closed_leaf_location, interaction, interactable, opening=True)
    npc_b = max(npcs, key=lambda actor: actor.get_actor_location().x)
    player.set_actor_location(npc_b.get_actor_location() - unreal.Vector(150.0, 0.0, 0.0), False, False)
    controller.set_control_rotation(unreal.Rotator())
    yield
    yield
    yield from press_e(world, controller)
    require(bool(property_value(presentation, "DialogueVisible")), "Reset test must leave an exchange active")

    unreal.log("T02_INTERACTION_FUNCTIONAL_TEST_PASSED")
    level_subsystem.editor_request_end_play()
    yield from wait_for(lambda: not unreal.EditorLevelLibrary.get_pie_worlds(False), "The first play session did not end")
    level_subsystem.editor_request_begin_play()
    yield from wait_for(lambda: bool(unreal.EditorLevelLibrary.get_pie_worlds(False)), "A fresh play session did not start")
    world = unreal.EditorLevelLibrary.get_pie_worlds(False)[0]
    yield from wait_for(lambda: len(unreal.GameplayStatics.get_all_actors_of_class(world, player_class)) == 1, "Fresh Player did not spawn")
    player = unreal.GameplayStatics.get_player_pawn(world, 0)
    controller = unreal.GameplayStatics.get_player_controller(world, 0)
    yield
    yield
    require(not bool(property_value(controller.get_hud(), "DialogueVisible")), "Launch must start without a dialogue panel")
    require(str(property_value(controller.get_hud(), "PromptText")) == "", "Fresh Room A spawn must start without Interaction Focus")
    player.set_actor_location(unreal.Vector(-200, 0, 90), False, False)
    controller.set_control_rotation(unreal.Rotator())
    yield
    yield
    require(str(property_value(controller.get_hud(), "PromptText")) == "E — Open", "Launch must restore the closed Door")
    yield from exercise_both_dialogues(world, player, controller, interactable_class, cycles=1)
    unreal.log("T03_DIALOGUE_FUNCTIONAL_TEST_PASSED")
    level_subsystem.editor_request_end_play()


unreal.AutomationScheduler.set_latent_command_timeout(60.0)
unreal.AutomationScheduler.add_latent_command(interaction_scenario())
