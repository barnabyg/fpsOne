"""Focused Player-world regression for the residents' neutral arm silhouette."""

import math

import unreal


MAP_ASSET = "/Game/Maps/L_Testbed"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def wait_for(predicate, message, frames=600):
    for _ in range(frames):
        if predicate():
            return
        yield
    raise AssertionError(message)


def visible_resident(npc):
    residents = [
        mesh
        for mesh in npc.get_components_by_class(unreal.SkeletalMeshComponent)
        if mesh.get_skeletal_mesh_asset() is not None and mesh.is_visible()
    ]
    require(len(residents) == 1, "Each NPC must present one visible imported resident")
    return residents[0]


def component_socket(resident, name):
    require(resident.does_socket_exist(name), f"Imported rig must retain its {name} marker")
    return resident.get_socket_transform(
        name, unreal.RelativeTransformSpace.RTS_COMPONENT
    ).translation


def joint_angle(origin, joint, end):
    first, second = origin - joint, end - joint
    cosine = (first.x * second.x + first.y * second.y + first.z * second.z) / (
        first.length() * second.length()
    )
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def pose_scenario():
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    require(level_subsystem.load_level(MAP_ASSET), "Could not load the testbed map")
    level_subsystem.editor_request_begin_play()
    yield from wait_for(
        lambda: bool(unreal.EditorLevelLibrary.get_pie_worlds(False)),
        "PIE world did not start",
    )
    world = unreal.EditorLevelLibrary.get_pie_worlds(False)[0]
    yield from wait_for(
        lambda: len(
            unreal.GameplayStatics.get_all_actors_with_tag(
                world, unreal.Name("DialogueNPC")
            )
        )
        == 2,
        "Both dialogue occupants must exist",
    )
    npcs = sorted(
        unreal.GameplayStatics.get_all_actors_with_tag(
            world, unreal.Name("DialogueNPC")
        ),
        key=lambda actor: actor.get_actor_location().x,
    )
    residents = [visible_resident(npc) for npc in npcs]
    for _ in range(180):
        yield

    failures = []
    for index, resident in enumerate(residents, start=1):
        for side in ("L", "R"):
            shoulder = component_socket(resident, "upperarm01_" + side)
            elbow = component_socket(resident, "lowerarm01_" + side)
            wrist = component_socket(resident, "wrist_" + side)
            angle = joint_angle(shoulder, elbow, wrist)
            unreal.log(
                f"NPC_POSE_SAMPLE NPC {index} {side}: shoulder={shoulder} "
                f"elbow={elbow} wrist={wrist} elbow_angle={angle:.1f}"
            )
            if not 145 < angle < 175:
                failures.append(
                    f"NPC {index} {side} elbow must read as a softly bent resting arm; "
                    f"got {angle:.1f} degrees"
                )
            index_knuckle = component_socket(resident, "finger2-1_" + side)
            little_knuckle = component_socket(resident, "finger5-1_" + side)
            index_distal = component_socket(resident, "finger2-3_" + side)
            little_distal = component_socket(resident, "finger5-3_" + side)
            fan_ratio = (index_distal - little_distal).length() / (
                index_knuckle - little_knuckle
            ).length()
            unreal.log(f"NPC_HAND_FAN NPC {index} {side}: {fan_ratio:.3f}")
            if fan_ratio >= 1.30:
                failures.append(
                    f"NPC {index} {side} fingers must rest in a curved hand rather than "
                    f"a rigid fan; distal-to-knuckle spread ratio was {fan_ratio:.3f}"
                )

    level_subsystem.editor_request_end_play()
    yield from wait_for(
        lambda: not unreal.EditorLevelLibrary.get_pie_worlds(False),
        "PIE world did not end",
    )
    require(not failures, "; ".join(failures))
    unreal.log("NPC_NEUTRAL_POSE_PASSED")


unreal.AutomationScheduler.set_latent_command_timeout(30.0)
unreal.AutomationScheduler.add_latent_command(pose_scenario())
