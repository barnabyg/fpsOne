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
NPC_PRESENTATIONS = (
    dict(rest_yaw=0, approach_direction=1.0, view_yaw=180.0,
         gesture_wrist='wrist_R', extended_presentation=False),
    dict(rest_yaw=180, approach_direction=-1.0, view_yaw=0.0,
         gesture_wrist='wrist_L', extended_presentation=True),
)


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


def smooth_resident_motion(world, resident, steps, wrist='wrist_R', settle_seconds=3.2):
    """Observe the resident through input and any deferred clip transition."""
    require(resident.does_socket_exist(wrist), 'Imported rig must retain its wrist marker')
    previous = resident.get_socket_location(wrist)
    previous_time = unreal.GameplayStatics.get_time_seconds(world)
    owner = resident.get_owner()
    owner_location = owner.get_actor_location()
    planted_feet = (resident.get_socket_location('foot_L'), resident.get_socket_location('foot_R'))

    def observe_frame():
        nonlocal previous, previous_time
        current = resident.get_socket_location(wrist)
        now = unreal.GameplayStatics.get_time_seconds(world)
        elapsed = max(0, now - previous_time)
        wrist_travel = (current - previous).length()
        # Generous motion bound: a restrained hand must not jump tens of cm
        # in a frame. Time scaling keeps this meaningful in headless and RHI runs.
        # The clips are baked at 30 fps, so a rendered frame can legitimately
        # consume a complete authored sample even when the headless world ticks
        # faster. Evaluate velocity over at least one baked sample while still
        # rejecting the tens-of-centimetres discontinuity caused by a pose reset.
        require(wrist_travel < 250 * max(elapsed, 1 / 30) + 1,
                f'NPC transition must not snap the resident arm to another pose; '
                f'wrist moved {wrist_travel:.2f} cm in {elapsed:.4f} seconds at clip '
                f'position {resident.get_position():.2f}')
        require((owner.get_actor_location() - owner_location).length() < 0.1,
                'NPC acknowledgement and clip transitions must not translate the resident')
        for side, planted in zip(('foot_L', 'foot_R'), planted_feet):
            require((resident.get_socket_location(side) - planted).length() < 4,
                    'NPC transition must retain visibly planted world-space feet')
        previous, previous_time = current, now

    for _ in steps:
        yield
        observe_frame()
    deadline = unreal.GameplayStatics.get_time_seconds(world) + settle_seconds
    while unreal.GameplayStatics.get_time_seconds(world) < deadline:
        yield
        observe_frame()


def visible_resident(npc):
    residents = [mesh for mesh in npc.get_components_by_class(unreal.SkeletalMeshComponent)
                 if mesh.get_skeletal_mesh_asset() is not None and mesh.is_visible()]
    require(len(residents) == 1, 'Each NPC must present one visible imported resident')
    return residents[0]


def component_socket(resident, name):
    require(resident.does_socket_exist(name), f'Imported rig must retain its {name} marker')
    return resident.get_socket_transform(
        name, unreal.RelativeTransformSpace.RTS_COMPONENT).translation


def component_rotation(resident, name):
    require(resident.does_socket_exist(name), f'Imported rig must retain its {name} marker')
    return resident.get_socket_transform(
        name, unreal.RelativeTransformSpace.RTS_COMPONENT).rotation


def joint_angle(origin, joint, end):
    first, second = origin - joint, end - joint
    cosine = (first.x * second.x + first.y * second.y + first.z * second.z) / (
        first.length() * second.length())
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def observe_acknowledgement(world, player, npc, resident, rest_yaw, wrist):
    """Exercise the restrained turn and return while monitoring the full transition."""
    def transition_steps():
        radians = math.radians(rest_yaw + 60)
        npc_location = npc.get_actor_location()
        player.set_actor_location(
            npc_location + unreal.Vector(200 * math.cos(radians), 200 * math.sin(radians), 0),
            False, False)
        turn_deadline = unreal.GameplayStatics.get_time_seconds(world) + 5
        while abs((npc.get_actor_rotation().yaw - rest_yaw + 180) % 360 - 180) < 3:
            require(unreal.GameplayStatics.get_time_seconds(world) < turn_deadline,
                    'Nearby NPC must begin a restrained acknowledgement turn')
            yield
        player.set_actor_location(unreal.Vector(-500, 500, 90), False, False)
        return_deadline = unreal.GameplayStatics.get_time_seconds(world) + 5
        while abs((npc.get_actor_rotation().yaw - rest_yaw + 180) % 360 - 180) > 0.5:
            require(unreal.GameplayStatics.get_time_seconds(world) < return_deadline,
                    'NPC must return smoothly to its authored rest direction')
            yield

    yield from smooth_resident_motion(
        world, resident, transition_steps(), wrist=wrist, settle_seconds=0)


def observe_residents_at_rest(world, player, npcs):
    """Observe the shipped presentation rather than the authored curve data."""
    player.set_actor_location(unreal.Vector(-500, 500, 90), False, False)
    residents = [visible_resident(npc) for npc in npcs]
    for _ in range(300):
        yield

    samples = [[] for _ in residents]
    feet = [
        (component_socket(resident, 'foot_L'), component_socket(resident, 'foot_R'))
        for resident in residents
    ]
    world_feet = [
        (resident.get_socket_location('foot_L'), resident.get_socket_location('foot_R'))
        for resident in residents
    ]
    start = unreal.GameplayStatics.get_time_seconds(world)
    next_sample = start
    while unreal.GameplayStatics.get_time_seconds(world) - start < 24.0:
        now = unreal.GameplayStatics.get_time_seconds(world)
        if now >= next_sample:
            for index, resident in enumerate(residents):
                left_foot, right_foot = component_socket(resident, 'foot_L'), component_socket(resident, 'foot_R')
                require((left_foot - feet[index][0]).length() < 0.5 and
                        (right_foot - feet[index][1]).length() < 0.5,
                        f'NPC {index + 1} must keep both feet planted throughout idle')
                require((resident.get_socket_location('foot_L') - world_feet[index][0]).length() < 0.75 and
                        (resident.get_socket_location('foot_R') - world_feet[index][1]).length() < 0.75,
                        f'NPC {index + 1} feet must not slide through the world throughout idle')
                head = component_socket(resident, 'head')
                samples[index].append(dict(
                    head=head,
                    wrist_left=component_socket(resident, 'wrist_L'),
                    wrist_right=component_socket(resident, 'wrist_R'),
                    torso_rotation=component_rotation(resident, 'spine02')))
            next_sample += 1.0
        yield

    require(all(len(resident_samples) >= 24 for resident_samples in samples),
            'Idle observation must cover at least 24 one-second samples')
    for index, (resident, resident_samples) in enumerate(zip(residents, samples)):
        # A short loop exposes itself when the same head-and-hand pose returns at
        # eight-second offsets. A 24-second authored performance must differ.
        repeat_deltas = []
        for sample_index in range(8):
            first, second, third = (resident_samples[sample_index],
                                    resident_samples[sample_index + 8],
                                    resident_samples[sample_index + 16])
            repeat_deltas.extend(
                sum((later[field] - earlier[field]).length()
                    for field in ('head', 'wrist_left', 'wrist_right'))
                for earlier, later in ((first, second), (second, third)))
        require(sum(delta > 0.25 for delta in repeat_deltas) >= len(repeat_deltas) // 2 and
                sum(repeat_deltas) / len(repeat_deltas) > 0.3,
                f'NPC {index + 1} idle must not expose an eight-second repeated beat')
        for side in ('L', 'R'):
            elbow = joint_angle(component_socket(resident, 'upperarm01_' + side),
                                component_socket(resident, 'lowerarm01_' + side),
                                component_socket(resident, 'wrist_' + side))
            unreal.log(f'T10_REST_ELBOW NPC {index + 1} {side}: {elbow:.1f} degrees')
            require(100 < elbow < 125,
                    f'NPC {index + 1} {side} elbow must remain softly bent at rest; got {elbow:.1f} degrees')
    # Compare centred torso motion so different bodies, hands, or static rest
    # poses cannot make synchronized whole-body sway appear distinct.
    correlations = {}
    for axis in ('x', 'y', 'z'):
        signals = []
        for resident_samples in samples:
            signals.append([
                getattr(sample['torso_rotation'], axis)
                for sample in resident_samples[:24]
            ])
        if min(max(signal) - min(signal) for signal in signals) < 0.00001:
            continue
        centred = [[value - sum(signal) / len(signal) for value in signal]
                   for signal in signals]
        denominator = math.sqrt(sum(value * value for value in centred[0]) *
                                sum(value * value for value in centred[1]))
        correlations[axis] = abs(sum(first * second for first, second in zip(*centred)) /
                                 denominator)
    unreal.log(f'T10_IDLE_CORRELATIONS: {correlations}')
    require(correlations and max(correlations.values()) < 0.9,
            f'NPC A and NPC B must not share synchronized whole-body sway; correlations {correlations}')
    for npc, resident, presentation in zip(npcs, residents, NPC_PRESENTATIONS):
        yield from observe_acknowledgement(
            world, player, npc, resident, presentation['rest_yaw'],
            presentation['gesture_wrist'])
    unreal.log('T10_NPC_ANIMATION_PASSED')


def capture_presentation(world, controller, name):
    """Optional rendered evidence; the normal functional run remains headless."""
    if "-T03Capture" not in unreal.SystemLibrary.get_command_line():
        return
    # Keep the UI pixel comparison against the static floor beside the animated
    # resident. The separate T06 capture shows the actual conversational view.
    original_view = controller.get_control_rotation()
    controller.set_control_rotation(unreal.Rotator(pitch=-20, yaw=150))
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
    controller.set_control_rotation(original_view)


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
    marker = {'-T06Capture': 'T06', '-T07Capture': 'T07'}.get(flag, 'T05')
    unreal.log("T04_ROOM_A_CAPTURE_PASSED" if flag == "-T04Capture" else f"{marker}_CAPTURE_PASSED {name}")


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


def exercise_both_dialogues(world, player, controller, interactable_class, interaction, cycles=3):
    npcs = sorted(unreal.GameplayStatics.get_all_actors_with_tag(world, unreal.Name("DialogueNPC")), key=lambda actor: actor.get_actor_location().x)
    expected_exchanges = (
        ("Resident A: The light is warm in here this afternoon.", "Player: It is a quiet place to take a break.", "Resident A: You are welcome to look around."),
        ("Resident B: I have just finished tidying the desk.", "Player: The room looks ready for the evening.", "Resident B: Yes, there is nothing else to do for now."),
    )
    presentation = controller.get_hud()
    require(len(npcs) == 2, "Both dialogue occupants must exist on launch")
    for index, npc in enumerate(npcs):
        npc_presentation = NPC_PRESENTATIONS[index]
        require(npc.get_component_by_class(interactable_class) is not None, "NPC must supply the shared Interactable contract")
        residents = [mesh for mesh in npc.get_components_by_class(unreal.SkeletalMeshComponent)
                     if mesh.get_skeletal_mesh_asset() is not None and mesh.is_visible()]
        require(len(residents) == 1, f'NPC {index + 1} must present one visible imported resident')
        resident = residents[0]
        require(135 < resident.get_socket_location('head').z - npc.get_actor_location().z + 90 < 190,
                'Both residents must idle at adult standing height')
        direction = npc_presentation['approach_direction']
        start = npc.get_actor_location() + unreal.Vector(direction * 150.0, 0.0, 0.0)
        player.set_actor_location(start, False, False)
        controller.set_control_rotation(unreal.Rotator(yaw=npc_presentation['view_yaw']))
        yield
        player.set_actor_location(npc.get_actor_location() - unreal.Vector(direction * 100.0, 0.0, 0.0), True, False)
        require((player.get_actor_location().x - npc.get_actor_location().x) * direction > 50.0, "The NPC capsule must block the Player")
        player.set_actor_location(start, False, False)
        yield
        yield
        for cycle in range(cycles):
            require(str(property_value(presentation, "PromptText")) == "E — Talk", "Either NPC must present the shared Talk prompt")
            for line_index, expected in enumerate(expected_exchanges[index]):
                activation = press_e(world, controller)
                if line_index == 0:
                    yield from smooth_resident_motion(
                        world, resident, activation,
                        npc_presentation['gesture_wrist'])
                else:
                    yield from activation
                require(bool(property_value(presentation, "DialogueVisible")), "The shared dialogue panel must be visible")
                require(str(property_value(presentation, "DialogueText")) == expected, "Either NPC must replay its own speaker-labelled lines in order")
                require(135 < resident.get_socket_location('head').z - npc.get_actor_location().z + 90 < 190,
                        'Both residents must keep adult standing height throughout dialogue')
            if npc_presentation['extended_presentation'] and cycle == 0 and cycles > 1:
                yield from exercise_npc_b_presentation(world, player, controller, npc, resident, interaction)
            yield from smooth_resident_motion(world, resident, press_e(world, controller),
                                              npc_presentation['gesture_wrist'])
            require(not bool(property_value(presentation, "DialogueVisible")), "Either exchange must dismiss after its last line")
            require(controller.get_hud() == presentation, "Both NPCs must reuse the same presentation")
            require(str(property_value(presentation, 'PromptText')) == 'E — Talk',
                    'Either exchange must immediately restore scanning and its Talk prompt')
            if npc_presentation['extended_presentation'] and cycle == 0 and cycles > 1:
                before = player.get_actor_location()
                yield from hold_input(world, controller, 'S', 12)
                require((player.get_actor_location() - before).length() > 5,
                        'NPC B dismissal must restore walking')
                yaw = controller.get_control_rotation().yaw
                yield from hold_input(world, controller, 'MouseX', 20, 20)
                require(abs((controller.get_control_rotation().yaw - yaw + 180) % 360 - 180) > 40,
                        'NPC B dismissal must restore unrestricted look')
                player.set_actor_location(start, False, False)
                controller.set_control_rotation(unreal.Rotator())
                yield
                yield


def exercise_npc_b_presentation(world, player, controller, npc, resident, interaction):
    """Observe NPC B's presentation and suspended controls through a real exchange."""
    yield from exercise_dialogue_controls(world, player, controller, interaction)
    controller.set_control_rotation(unreal.Rotator())
    yield from wait_for_resident_gestures(resident, 'wrist_L')
    require(abs((npc.get_actor_rotation().yaw - 180 + 180) % 360 - 180) < 12.1,
            'NPC B must acknowledge the Player around its Room B facing direction')


def exercise_dialogue_controls(world, player, controller, interaction):
    """The same Player input contract applies while either resident speaks."""
    stationary = player.get_actor_location()
    for key in ('W', 'S', 'A', 'D'):
        yield from hold_input(world, controller, key, 12)
        require((player.get_actor_location() - stationary).length() < 1,
                f'Dialogue must suspend {key} walking')
    for key, axis, limit in (('MouseX', 'yaw', 35.1), ('MouseY', 'pitch', 20.1)):
        before = getattr(controller.get_control_rotation(), axis)
        yield from hold_input(world, controller, key, 20, 20)
        difference = (getattr(controller.get_control_rotation(), axis) - before + 180) % 360 - 180
        require(2 < abs(difference) <= limit, f'Dialogue must retain bounded {axis}')
    require(property_value(interaction, 'CurrentFocus') is None,
            'Dialogue must keep Interaction scanning suspended')
    return stationary


def wait_for_resident_gestures(resident, wrist):
    """Detect two separated gesture beats without coupling the test to curve timings."""
    yield from wait_for(lambda: 0.35 < resident.get_position() < 0.65,
                        'The resident must reach its conversational rest pose', frames=7200)
    resting_wrist = resident.get_socket_location(wrist)
    beats = 0
    active = False
    for _ in range(7200):
        travel = (resident.get_socket_location(wrist) - resting_wrist).length()
        if not active and travel > 5:
            beats += 1
            active = True
            if beats == 2:
                return
        elif active and travel < 3:
            active = False
        yield
    raise AssertionError('The resident must make two visible gesture beats separated by a rest pose')


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
    # Approach the clear south window bay at standing height. Test the complete
    # window assembly's containment, rather than assuming which part blocks it.
    player.set_actor_location(unreal.Vector(200, -65, 90), False, False)
    player.set_actor_location(unreal.Vector(300, -65, 90), True, False)
    require((player.get_actor_location() - unreal.Vector(300, -65, 90)).length() < 5,
            "The Player must reach the clear approach to the Room B window")
    player.set_actor_location(unreal.Vector(500, -65, 90), True, False)
    window_stop = player.get_actor_location()
    unreal.log(f"T05_WINDOW_CONTAINMENT: {window_stop}")
    require(350 < window_stop.x < 420,
            f"Room B window must block the Player at the exterior boundary: {window_stop}")
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

    npcs = sorted(
        unreal.GameplayStatics.get_all_actors_with_tag(world, unreal.Name("DialogueNPC")),
        key=lambda actor: actor.get_actor_location().x)
    require(len(npcs) == 2, "Each Room must contain one Dialogue NPC")
    require(
        sum(npc.get_actor_location().x < 0.0 for npc in npcs) == 1,
        "NPCs must occupy different Rooms",
    )
    yield from observe_residents_at_rest(world, player, npcs)
    npc = min(npcs, key=lambda actor: actor.get_actor_location().x)
    # Observe the imported rig in the running world, including animation scale.
    # The editable MPFB source publishes its anatomical head marker. A valid
    # bind mesh alone cannot catch FBX clips collapsing to metre-sized bones.
    residents = [mesh for mesh in npc.get_components_by_class(unreal.SkeletalMeshComponent)
                 if mesh.get_skeletal_mesh_asset() is not None and mesh.is_visible()]
    require(len(residents) == 1, 'NPC A must present one visible imported resident')
    resident = residents[0]
    require(135 < resident.get_socket_location('head').z - npc.get_actor_location().z + 90 < 190,
            'NPC A animated head must remain at adult standing height')
    player.set_actor_location(npc.get_actor_location() + unreal.Vector(150.0, 0.0, 0.0), False, False)
    controller.set_control_rotation(unreal.Rotator(yaw=180.0))
    yield
    yield
    require(str(property_value(interaction, "CurrentPrompt")) == "E — Talk", "Focused NPC must offer E — Talk")
    yield from smooth_resident_motion(world, resident, press_e(world, controller))
    presentation = controller.get_hud()
    require(bool(property_value(presentation, "DialogueVisible")), "E must open the dialogue panel")
    require(135 < resident.get_socket_location('head').z - npc.get_actor_location().z + 90 < 190,
            'Conversational animation must preserve adult standing height')
    require(str(property_value(presentation, "DialogueText")) == "Resident A: The light is warm in here this afternoon.", f"E must present NPC A's initial speaker-labelled line; got {property_value(presentation, 'DialogueText')}")
    yield from capture_room(world, controller, 'npc-a-conversation', 'NPCAReview', '-T06Capture')
    yield from capture_presentation(world, controller, "npc-a-dialogue")
    yield from press_e(world, controller)
    require(str(property_value(presentation, "DialogueText")) == "Player: It is a quiet place to take a break.", "E must advance exactly one dialogue line")
    yield from press_e(world, controller)
    require(str(property_value(presentation, "DialogueText")) == "Resident A: You are welcome to look around.", "The final line must remain visible until E")
    # Schedule E near the visible gesture's peak, then observe actual bone
    # motion across dismissal and immediate replay through the Player input.
    yield from wait_for_resident_gestures(resident, 'wrist_R')
    yield from smooth_resident_motion(world, resident, press_e(world, controller))
    require(not bool(property_value(presentation, "DialogueVisible")), "E after the final line must dismiss dialogue")
    yield from smooth_resident_motion(world, resident, press_e(world, controller))
    require(str(property_value(presentation, "DialogueText")) == "Resident A: The light is warm in here this afternoon.", "A replay must start from the first line")
    require(property_value(interaction, "CurrentFocus") is None, "Dialogue must suspend Interaction scanning")
    require(str(property_value(presentation, "PromptText")) == "", "Dialogue must hide the Interaction Prompt")
    stationary = yield from exercise_dialogue_controls(world, player, controller, interaction)
    for _ in range(3):
        yield from press_e(world, controller)
    require(not bool(property_value(presentation, "DialogueVisible")), "Dialogue completion must restore exploration presentation")
    return_deadline = unreal.GameplayStatics.get_time_seconds(world) + 4.1
    yield from smooth_resident_motion(world, resident, wait_for(
        lambda: unreal.GameplayStatics.get_time_seconds(world) >= return_deadline,
        'The resident must finish returning to rest', frames=2400), settle_seconds=0)
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
    yield from exercise_both_dialogues(world, player, controller, interactable_class, interaction)

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
    yield from capture_room(world, controller, 'npc-b-conversation', 'NPCBReview', '-T07Capture')

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
    interaction = player.get_component_by_class(interaction_class)
    yield from exercise_both_dialogues(world, player, controller, interactable_class, interaction, cycles=1)
    unreal.log("T03_DIALOGUE_FUNCTIONAL_TEST_PASSED")
    level_subsystem.editor_request_end_play()


unreal.AutomationScheduler.set_latent_command_timeout(180.0)
unreal.AutomationScheduler.add_latent_command(interaction_scenario())
