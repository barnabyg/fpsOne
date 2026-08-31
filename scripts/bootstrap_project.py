"""Generate the project-authored T02 Blueprint assets with Unreal Editor 5.8."""

import os
import sys
import unreal

sys.path.insert(0, os.path.dirname(__file__))
sys.dont_write_bytecode = True
from interaction_assets import (
    INTERACTION_ASSET_PATHS,
    configure_player_interaction,
    create_interaction_assets,
    require_asset_absent,
)
from dialogue_assets import DIALOGUE_ASSET_PATHS, create_npc_assets


PLAYER_ASSET = "/Game/Blueprints/BP_Player"
PLAYER_CONTROLLER_ASSET = "/Game/Blueprints/BP_TestbedPlayerController"
GAME_MODE_ASSET = "/Game/Blueprints/BP_TestbedGameMode"
MAP_ASSET = "/Game/Maps/L_Testbed"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def connect(output_pin, input_pin, description: str) -> None:
    require(output_pin.try_create_connection(input_pin), f"Could not connect {description}")


def add_axis_binding(event_graph, axis_name: str, function_path: str, y: int) -> None:
    input_node = event_graph.create_node_from_name(
        f"Input|AxisEvents|{axis_name}", unreal.Vector2D(-700.0, float(y)), []
    )
    require(input_node is not None, f"Could not create the {axis_name} input event")

    function_node = event_graph.add_call_function_node(function_path)
    require(function_node is not None, f"Could not create the {function_path} call")
    function_node.set_node_pos(unreal.IntPoint(-360, y))

    connect(
        input_node.find_then_pin(),
        function_node.find_execute_pin(),
        f"{axis_name} execution",
    )
    connect(
        input_node.find_output_pin("AxisValue"),
        function_node.find_input_pin("Val"),
        f"{axis_name} value",
    )


def add_directional_movement_binding(
    event_graph, axis_name: str, direction_function_path: str, y: int
) -> None:
    input_node = event_graph.create_node_from_name(
        f"Input|AxisEvents|{axis_name}", unreal.Vector2D(-700.0, float(y)), []
    )
    require(input_node is not None, f"Could not create the {axis_name} input event")

    direction_node = event_graph.add_call_function_node(direction_function_path)
    require(
        direction_node is not None,
        f"Could not create the {direction_function_path} call",
    )
    direction_node.set_node_pos(unreal.IntPoint(-420, y + 80))

    movement_node = event_graph.add_call_function_node(
        "/Script/Engine.Pawn:AddMovementInput"
    )
    require(movement_node is not None, "Could not create the Add Movement Input call")
    movement_node.set_node_pos(unreal.IntPoint(-120, y))

    connect(
        input_node.find_then_pin(),
        movement_node.find_execute_pin(),
        f"{axis_name} execution",
    )
    connect(
        direction_node.find_output_pin("ReturnValue"),
        movement_node.find_input_pin("WorldDirection"),
        f"{axis_name} horizontal direction",
    )
    connect(
        input_node.find_output_pin("AxisValue"),
        movement_node.find_input_pin("ScaleValue"),
        f"{axis_name} value",
    )


def build_player_graph(blueprint: unreal.Blueprint) -> None:
    event_graph = unreal.BlueprintGraphEditor.get_graph_editor_by_name(
        blueprint, "EventGraph"
    )
    require(event_graph is not None, "BP_Player has no EventGraph")

    existing_nodes = event_graph.list_all_nodes()
    if existing_nodes:
        event_graph.remove_nodes(existing_nodes)

    add_directional_movement_binding(
        event_graph,
        "MoveForward",
        "/Script/Engine.Actor:GetActorForwardVector",
        -420,
    )
    add_directional_movement_binding(
        event_graph,
        "MoveRight",
        "/Script/Engine.Actor:GetActorRightVector",
        -120,
    )
    add_axis_binding(
        event_graph, "Turn", "/Script/Engine.Pawn:AddControllerYawInput", 180
    )
    add_axis_binding(
        event_graph, "LookUp", "/Script/Engine.Pawn:AddControllerPitchInput", 420
    )

    exit_node = event_graph.create_node_from_name(
        "Input|ActionEvents|Exit", unreal.Vector2D(-700.0, 660.0), []
    )
    require(exit_node is not None, "Could not create the Exit input event")
    quit_node = event_graph.add_call_function_node(
        "/Script/Engine.KismetSystemLibrary:QuitGame"
    )
    require(quit_node is not None, "Could not create the Quit Game call")
    quit_node.set_node_pos(unreal.IntPoint(-360, 660))
    connect(
        exit_node.find_output_pin("Pressed"),
        quit_node.find_execute_pin(),
        "Escape press to Quit Game",
    )


def create_player_blueprint(interaction_blueprint) -> unreal.Blueprint:
    require_asset_absent(PLAYER_ASSET)
    blueprint = unreal.BlueprintEditorLibrary.create_blueprint_asset_with_parent(
        PLAYER_ASSET, unreal.Character
    )
    require(blueprint is not None, "Could not create BP_Player")

    build_player_graph(blueprint)
    configure_player_interaction(blueprint, interaction_blueprint)
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)

    player_defaults = unreal.get_default_object(blueprint.generated_class())
    player_defaults.set_editor_property("use_controller_rotation_pitch", False)
    player_defaults.set_editor_property("use_controller_rotation_yaw", True)
    player_defaults.set_editor_property("use_controller_rotation_roll", False)
    player_defaults.set_editor_property("base_eye_height", 64.0)

    movement_component = player_defaults.get_component_by_class(
        unreal.CharacterMovementComponent
    )
    require(
        movement_component is not None,
        "BP_Player has no inherited Character Movement component",
    )
    movement_component.set_editor_property("gravity_scale", 1.0)
    movement_component.set_editor_property("max_walk_speed", 450.0)
    movement_component.set_editor_property(
        "default_land_movement_mode", unreal.MovementMode.MOVE_WALKING
    )

    mesh_component = player_defaults.get_component_by_class(unreal.SkeletalMeshComponent)
    require(mesh_component is not None, "BP_Player has no inherited mesh component")
    mesh_component.set_editor_property("hidden_in_game", True)
    mesh_component.set_visibility(False)

    graph_editor = unreal.BlueprintGraphEditor.get_graph_editor_by_name(
        blueprint, "EventGraph"
    )
    require(not graph_editor.list_nodes_with_errors(), "BP_Player graph contains errors")
    require(not graph_editor.list_nodes_with_warnings(), "BP_Player graph contains warnings")
    unreal.EditorAssetLibrary.save_loaded_asset(blueprint, only_if_is_dirty=False)
    return blueprint


def create_player_controller_blueprint() -> unreal.Blueprint:
    require_asset_absent(PLAYER_CONTROLLER_ASSET)
    blueprint = unreal.BlueprintEditorLibrary.create_blueprint_asset_with_parent(
        PLAYER_CONTROLLER_ASSET, unreal.PlayerController
    )
    require(blueprint is not None, "Could not create BP_TestbedPlayerController")
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    controller_defaults = unreal.get_default_object(blueprint.generated_class())
    controller_defaults.set_editor_property("enable_motion_controls", False)
    unreal.EditorAssetLibrary.save_loaded_asset(blueprint, only_if_is_dirty=False)
    return blueprint


def create_game_mode_blueprint(
    player_blueprint: unreal.Blueprint,
    player_controller_blueprint: unreal.Blueprint,
    hud_blueprint: unreal.Blueprint,
) -> unreal.Blueprint:
    require_asset_absent(GAME_MODE_ASSET)
    blueprint = unreal.BlueprintEditorLibrary.create_blueprint_asset_with_parent(
        GAME_MODE_ASSET, unreal.GameModeBase
    )
    require(blueprint is not None, "Could not create BP_TestbedGameMode")
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    game_mode_defaults = unreal.get_default_object(blueprint.generated_class())
    game_mode_defaults.set_editor_property(
        "default_pawn_class", player_blueprint.generated_class()
    )
    game_mode_defaults.set_editor_property(
        "player_controller_class", player_controller_blueprint.generated_class()
    )
    game_mode_defaults.set_editor_property("hud_class", hud_blueprint.generated_class())
    unreal.EditorAssetLibrary.save_loaded_asset(blueprint, only_if_is_dirty=False)
    return blueprint


def spawn_mesh_actor(
    actor_subsystem,
    mesh,
    label: str,
    location: unreal.Vector,
    scale: unreal.Vector,
) -> unreal.StaticMeshActor:
    actor = actor_subsystem.spawn_actor_from_class(
        unreal.StaticMeshActor, location, unreal.Rotator()
    )
    require(actor is not None, f"Could not spawn {label}")
    actor.set_actor_label(label)
    actor.set_actor_scale3d(scale)
    component = actor.get_editor_property("static_mesh_component")
    component.set_static_mesh(mesh)
    component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
    return actor


def create_testbed_map(
    game_mode_blueprint: unreal.Blueprint,
    door_blueprint: unreal.Blueprint,
    interaction_test_target_blueprint: unreal.Blueprint,
    npc_blueprint: unreal.Blueprint,
) -> None:
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    require_asset_absent(MAP_ASSET)
    require(level_subsystem.new_level(MAP_ASSET, False), "Could not create L_Testbed")

    cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
    require(cube is not None, "Could not load the engine cube primitive")

    # T02 blockout: a 6 x 5 m Room A joins a 4 x 4 m Room B directly through
    # one Door opening. Engine primitives keep this functional slice asset-free.
    spawn_mesh_actor(
        actor_subsystem,
        cube,
        "RoomA_Floor",
        unreal.Vector(-300.0, 0.0, -10.0),
        unreal.Vector(6.0, 5.0, 0.2),
    )
    spawn_mesh_actor(
        actor_subsystem,
        cube,
        "RoomA_Ceiling",
        unreal.Vector(-300.0, 0.0, 280.0),
        unreal.Vector(6.0, 5.0, 0.2),
    )
    spawn_mesh_actor(
        actor_subsystem,
        cube,
        "RoomA_NorthWall",
        unreal.Vector(-300.0, 250.0, 135.0),
        unreal.Vector(6.0, 0.2, 2.7),
    )
    spawn_mesh_actor(
        actor_subsystem,
        cube,
        "RoomA_SouthWall",
        unreal.Vector(-300.0, -250.0, 135.0),
        unreal.Vector(6.0, 0.2, 2.7),
    )
    spawn_mesh_actor(
        actor_subsystem,
        cube,
        "RoomA_WestWall",
        unreal.Vector(-600.0, 0.0, 135.0),
        unreal.Vector(0.2, 5.0, 2.7),
    )
    spawn_mesh_actor(
        actor_subsystem,
        cube,
        "SharedWall_North",
        unreal.Vector(0.0, 150.0, 135.0),
        unreal.Vector(0.2, 2.0, 2.7),
    )
    spawn_mesh_actor(
        actor_subsystem,
        cube,
        "SharedWall_South",
        unreal.Vector(0.0, -150.0, 135.0),
        unreal.Vector(0.2, 2.0, 2.7),
    )

    spawn_mesh_actor(actor_subsystem, cube, "RoomB_Floor", unreal.Vector(200.0, 0.0, -10.0), unreal.Vector(4.0, 4.0, 0.2))
    spawn_mesh_actor(actor_subsystem, cube, "RoomB_Ceiling", unreal.Vector(200.0, 0.0, 280.0), unreal.Vector(4.0, 4.0, 0.2))
    spawn_mesh_actor(actor_subsystem, cube, "RoomB_NorthWall", unreal.Vector(200.0, 200.0, 135.0), unreal.Vector(4.0, 0.2, 2.7))
    spawn_mesh_actor(actor_subsystem, cube, "RoomB_SouthWall", unreal.Vector(200.0, -200.0, 135.0), unreal.Vector(4.0, 0.2, 2.7))
    spawn_mesh_actor(actor_subsystem, cube, "RoomB_EastWall", unreal.Vector(400.0, 0.0, 135.0), unreal.Vector(0.2, 4.0, 2.7))

    primary_door = actor_subsystem.spawn_actor_from_class(
        door_blueprint.generated_class(), unreal.Vector(0.0, 0.0, 105.0), unreal.Rotator()
    )
    require(primary_door is not None, "Could not spawn the Door")
    primary_door.set_actor_label("Door")

    for label, location, lines in (
        ("NPC_A", unreal.Vector(-350.0, -130.0, 90.0), [
            "Resident A: The light is warm in here this afternoon.",
            "Player: It is a quiet place to take a break.",
            "Resident A: You are welcome to look around.",
        ]),
        ("NPC_B", unreal.Vector(250.0, 100.0, 90.0), [
            "Resident B: I have just finished tidying the desk.",
            "Player: The room looks ready for the evening.",
            "Resident B: Yes, there is nothing else to do for now.",
        ]),
    ):
        npc = actor_subsystem.spawn_actor_from_class(npc_blueprint.generated_class(), location, unreal.Rotator())
        require(npc is not None, f"Could not spawn {label}")
        npc.set_actor_label(label)
        npc.set_editor_property("tags", [unreal.Name("DialogueNPC")])
        npc.set_editor_property("DialogueLines", [unreal.Text(line) for line in lines])

    distractor = actor_subsystem.spawn_actor_from_class(
        interaction_test_target_blueprint.generated_class(),
        unreal.Vector(-40.0, 130.0, 105.0),
        unreal.Rotator(0.0, 90.0, 0.0),
    )
    require(distractor is not None, "Could not spawn the singular-focus distractor")
    distractor.set_actor_label("InteractionDistractor")

    occluder = spawn_mesh_actor(
        actor_subsystem, cube, "InteractionTestOccluder", unreal.Vector(-100.0, 180.0, 140.0), unreal.Vector(0.2, 0.8, 2.8)
    )
    occluder.get_editor_property("static_mesh_component").set_editor_property(
        "mobility", unreal.ComponentMobility.MOVABLE
    )
    occluder.set_editor_property("tags", [unreal.Name("InteractionTestOccluder")])

    player_start = actor_subsystem.spawn_actor_from_class(
        unreal.PlayerStart,
        unreal.Vector(-200.0, 0.0, 90.0),
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    require(player_start is not None, "Could not spawn PlayerStart")
    player_start.set_actor_label("PlayerStart_T02")

    sky_light = actor_subsystem.spawn_actor_from_class(
        unreal.SkyLight, unreal.Vector(0.0, 0.0, 250.0), unreal.Rotator()
    )
    require(sky_light is not None, "Could not spawn SkyLight")
    sky_light.set_actor_label("SkyLight_T02")

    directional_light = actor_subsystem.spawn_actor_from_class(
        unreal.DirectionalLight,
        unreal.Vector(0.0, 0.0, 250.0),
        unreal.Rotator(-40.0, -35.0, 0.0),
    )
    require(directional_light is not None, "Could not spawn DirectionalLight")
    directional_light.set_actor_label("DirectionalLight_T02")
    directional_light.get_editor_property("directional_light_component").set_editor_property(
        "intensity", 4.0
    )

    point_light = actor_subsystem.spawn_actor_from_class(
        unreal.PointLight, unreal.Vector(0.0, 0.0, 240.0), unreal.Rotator()
    )
    require(point_light is not None, "Could not spawn PointLight")
    point_light.set_actor_label("PointLight_T02")
    point_light.get_editor_property("point_light_component").set_editor_property(
        "intensity", 3500.0
    )

    editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = editor_subsystem.get_editor_world()
    world.get_world_settings().set_editor_property(
        "default_game_mode", game_mode_blueprint.generated_class()
    )

    require(level_subsystem.save_current_level(), "Could not save L_Testbed")
    require(
        unreal.EditorAssetLibrary.save_directory(
            "/Game", only_if_is_dirty=False, recursive=True
        ),
        "Could not save generated project assets",
    )


def main() -> None:
    for asset_path in (*INTERACTION_ASSET_PATHS, *DIALOGUE_ASSET_PATHS, PLAYER_ASSET, PLAYER_CONTROLLER_ASSET, GAME_MODE_ASSET, MAP_ASSET):
        require_asset_absent(asset_path)
    unreal.log(f"Generating T02 assets with {unreal.SystemLibrary.get_engine_version()}")
    (
        interactable_blueprint,
        interaction_blueprint,
        door_blueprint,
        hud_blueprint,
        interaction_test_target_blueprint,
    ) = create_interaction_assets()
    npc_blueprint = create_npc_assets(interactable_blueprint, interaction_blueprint)
    player_blueprint = create_player_blueprint(interaction_blueprint)
    player_controller_blueprint = create_player_controller_blueprint()
    game_mode_blueprint = create_game_mode_blueprint(
        player_blueprint, player_controller_blueprint, hud_blueprint
    )
    create_testbed_map(
        game_mode_blueprint, door_blueprint, interaction_test_target_blueprint, npc_blueprint
    )
    unreal.log("T02 Blueprint generation completed without script errors")


if __name__ == "__main__":
    main()
