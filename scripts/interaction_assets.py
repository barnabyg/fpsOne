"""Deterministically generate the project-authored T02 Interaction Blueprints."""

import unreal


INTERACTABLE_COMPONENT_ASSET = "/Game/Blueprints/BPC_Interactable"
DOOR_INTERACTABLE_COMPONENT_ASSET = "/Game/Blueprints/BPC_DoorInteractable"
INTERACTION_COMPONENT_ASSET = "/Game/Blueprints/BPC_Interaction"
DOOR_ASSET = "/Game/Blueprints/BP_Door"
HUD_ASSET = "/Game/Blueprints/BP_InteractionHUD"
TEST_INTERACTABLE_ASSET = "/Game/Blueprints/BP_InteractionTestTarget"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def connect(output_pin, input_pin, description):
    require(output_pin.try_create_connection(input_pin), f"Could not connect {description}")


def set_pin(pin, value, description):
    require(pin.is_valid(), f"Could not find pin for {description}")
    require(pin.set_pin_value(str(value)), f"Could not set {description} to {value}")


def delete_asset_if_present(asset_path):
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        require(unreal.EditorAssetLibrary.delete_asset(asset_path), f"Could not replace {asset_path}")


def compile_and_save(blueprint):
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    for graph_name in unreal.BlueprintEditorLibrary.list_graph_names(blueprint):
        graph = unreal.BlueprintGraphEditor.get_graph_editor_by_name(blueprint, graph_name)
        if graph is None:
            continue
        require(not graph.list_nodes_with_errors(), f"{blueprint.get_name()}:{graph_name} contains errors")
        require(not graph.list_nodes_with_warnings(), f"{blueprint.get_name()}:{graph_name} contains warnings")


def save_blueprint(blueprint):
    require(
        unreal.EditorAssetLibrary.save_loaded_asset(blueprint, only_if_is_dirty=False),
        f"Could not save {blueprint.get_name()}",
    )


def class_path(generated_class):
    return generated_class.get_path_name()


def add_component_with_handle(blueprint, component_class, name, parent_handle=None):
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsystem.k2_gather_subobject_data_for_blueprint(blueprint)
    require(handles, f"Could not gather components for {blueprint.get_name()}")
    params = unreal.AddNewSubobjectParams(
        parent_handle=handles[0] if parent_handle is None else parent_handle,
        new_class=component_class,
        blueprint_context=blueprint,
    )
    handle, failure = subsystem.add_new_subobject(params)
    require(
        unreal.SubobjectDataBlueprintFunctionLibrary.is_handle_valid(handle),
        f"Could not add {name}: {failure}",
    )
    require(subsystem.rename_subobject(handle, unreal.Text(name)), f"Could not name {name}")
    data = subsystem.k2_find_subobject_data_from_handle(handle)
    component = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, blueprint)
    require(component is not None, f"Could not resolve {name}")
    return component, handle


def add_component(blueprint, component_class, name):
    component, _ = add_component_with_handle(blueprint, component_class, name)
    return component


def add_function_call(graph, path, x, y, description):
    node = graph.add_call_function_node(path)
    require(node is not None, f"Could not add {description}")
    node.set_node_pos(unreal.IntPoint(x, y))
    return node


def add_get(graph, name, x, y, owner_class_path=""):
    node = graph.add_get_member_variable_node(name, owner_class_path)
    require(node is not None, f"Could not read {name}")
    node.set_node_pos(unreal.IntPoint(x, y))
    return node


def add_set(graph, name, x, y, owner_class_path=""):
    node = graph.add_set_member_variable_node(name, owner_class_path)
    require(node is not None, f"Could not write {name}")
    node.set_node_pos(unreal.IntPoint(x, y))
    return node


def member_value_pin(node, name):
    pin = node.find_input_pin(name)
    if pin.is_valid():
        return pin
    return node.find_data_input_pin()


def create_interactable_component():
    delete_asset_if_present(INTERACTABLE_COMPONENT_ASSET)
    blueprint = unreal.BlueprintEditorLibrary.create_blueprint_asset_with_parent(
        INTERACTABLE_COMPONENT_ASSET, unreal.ActorComponent
    )
    require(blueprint is not None, "Could not create BPC_Interactable")

    graph = unreal.BlueprintGraphEditor.create_and_edit_function_graph(blueprint, "RequestInteraction")
    require(graph.add_member_variable("InteractionAvailable", unreal.BlueprintEditorLibrary.get_basic_type_by_name("bool"), "true"), "Could not add InteractionAvailable")
    require(graph.add_member_variable("InteractionPrompt", unreal.BlueprintEditorLibrary.get_basic_type_by_name("text"), "E — Interact"), "Could not add InteractionPrompt")
    entry = graph.find_graph_entry_pin()
    available = add_get(graph, "InteractionAvailable", -480, 80)
    branch = graph.add_branch_node()
    branch.set_node_pos(unreal.IntPoint(-220, 0))
    connect(entry, branch.find_execute_pin(), "RequestInteraction entry")
    connect(available.find_result_pin(), branch.find_condition_pin(), "Interaction availability")
    graph.set_function_is_public()
    compile_and_save(blueprint)
    return blueprint


def create_door_interactable_component(interactable_blueprint):
    delete_asset_if_present(DOOR_INTERACTABLE_COMPONENT_ASSET)
    blueprint = unreal.BlueprintEditorLibrary.create_blueprint_asset_with_parent(
        DOOR_INTERACTABLE_COMPONENT_ASSET, interactable_blueprint.generated_class()
    )
    require(blueprint is not None, "Could not create BPC_DoorInteractable")
    require(
        blueprint.add_event_dispatcher("InteractionRequested"),
        "Could not add the Door Interaction dispatcher",
    )
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)

    override_graph = unreal.BlueprintEditorLibrary.add_function_override(blueprint, "RequestInteraction")
    require(override_graph is not None, "Could not override RequestInteraction for the Door")
    graph = unreal.BlueprintGraphEditor.get_graph_editor(override_graph)
    entry = graph.find_graph_entry_pin()
    for node in graph.list_all_nodes():
        if "Parent" in node.get_node_title():
            graph.remove_nodes([node])
    available = add_get(
        graph,
        "InteractionAvailable",
        -420,
        120,
    )
    branch = graph.add_branch_node()
    branch.set_node_pos(unreal.IntPoint(-160, 0))
    dispatch = graph.create_node_from_name(
        "Default|CallInteractionRequested", unreal.Vector2D(140.0, 0.0), []
    )
    require(dispatch is not None, "Could not call the Door Interaction dispatcher")
    self_reference = graph.create_node_from_name(
        "Variables|Getareferencetoself", unreal.Vector2D(-120.0, -200.0), []
    )
    require(self_reference is not None, "Could not resolve the Door Interactable self reference")
    connect(entry, branch.find_execute_pin(), "Door Interaction availability check")
    connect(available.find_result_pin(), branch.find_condition_pin(), "Door Interaction availability")
    connect(branch.find_then_pin(), dispatch.find_execute_pin(), "available Door Interaction")
    connect(self_reference.find_result_pin(), dispatch.find_self_pin(), "Door Interaction dispatcher target")
    compile_and_save(blueprint)
    return blueprint


def clear_focus_nodes(graph, execution_pin, x, y):
    set_focus = add_set(graph, "CurrentFocus", x, y)
    set_prompt = add_set(graph, "CurrentPrompt", x + 260, y)
    set_pin(member_value_pin(set_focus, "CurrentFocus"), "None", "cleared Interaction Focus")
    set_pin(member_value_pin(set_prompt, "CurrentPrompt"), "", "cleared Interaction Prompt")
    connect(execution_pin, set_focus.find_execute_pin(), "clear Interaction Focus")
    connect(set_focus.find_then_pin(), set_prompt.find_execute_pin(), "clear Interaction Prompt")


def create_interaction_component(interactable_blueprint):
    delete_asset_if_present(INTERACTION_COMPONENT_ASSET)
    blueprint = unreal.BlueprintEditorLibrary.create_blueprint_asset_with_parent(
        INTERACTION_COMPONENT_ASSET, unreal.ActorComponent
    )
    require(blueprint is not None, "Could not create BPC_Interaction")
    interactable_class = interactable_blueprint.generated_class()
    interactable_path = class_path(interactable_class)

    scan = unreal.BlueprintGraphEditor.create_and_edit_function_graph(blueprint, "ScanForInteractionFocus")
    require(scan.add_member_variable("CurrentFocus", unreal.BlueprintEditorLibrary.get_object_reference_type(interactable_class)), "Could not add CurrentFocus")
    require(scan.add_member_variable("CurrentPrompt", unreal.BlueprintEditorLibrary.get_basic_type_by_name("text"), ""), "Could not add CurrentPrompt")

    entry = scan.find_graph_entry_pin()
    camera = add_function_call(scan, "/Script/Engine.GameplayStatics:GetPlayerCameraManager", -900, -360, "player camera manager")
    set_pin(camera.find_input_pin("PlayerIndex"), "0", "camera player index")
    location = add_function_call(scan, "/Script/Engine.Actor:K2_GetActorLocation", -640, -430, "camera location")
    forward = add_function_call(scan, "/Script/Engine.Actor:GetActorForwardVector", -640, -260, "camera forward vector")
    connect(camera.find_result_pin(), location.find_self_pin(), "camera location target")
    connect(camera.find_result_pin(), forward.find_self_pin(), "camera forward target")

    scale = add_function_call(scan, "/Script/Engine.KismetMathLibrary:Multiply_VectorFloat", -360, -250, "250 cm trace vector")
    connect(forward.find_result_pin(), scale.find_input_pin("A"), "camera forward vector")
    set_pin(
        scale.find_input_pin("B"),
        "(X=250.0,Y=250.0,Z=250.0)",
        "Interaction range",
    )
    end = add_function_call(scan, "/Script/Engine.KismetMathLibrary:Add_VectorVector", -80, -300, "trace end")
    connect(location.find_result_pin(), end.find_input_pin("A"), "trace start to end")
    connect(scale.find_result_pin(), end.find_input_pin("B"), "scaled trace vector")

    trace = add_function_call(scan, "/Script/Engine.KismetSystemLibrary:LineTraceSingle", 220, -80, "view-centre trace")
    set_pin(trace.find_input_pin("TraceChannel"), "TraceTypeQuery1", "Visibility trace channel")
    set_pin(trace.find_input_pin("bTraceComplex"), "false", "simple trace")
    set_pin(trace.find_input_pin("DrawDebugType"), "None", "trace debug mode")
    set_pin(trace.find_input_pin("bIgnoreSelf"), "true", "ignore Player")
    connect(entry, trace.find_execute_pin(), "scan execution")
    connect(location.find_result_pin(), trace.find_input_pin("Start"), "trace start")
    connect(end.find_result_pin(), trace.find_input_pin("End"), "trace end")

    hit_branch = scan.add_branch_node()
    hit_branch.set_node_pos(unreal.IntPoint(520, -80))
    connect(trace.find_then_pin(), hit_branch.find_execute_pin(), "trace result")
    connect(trace.find_output_pin("ReturnValue"), hit_branch.find_condition_pin(), "blocking hit")
    clear_focus_nodes(scan, hit_branch.find_else_pin(), 820, 260)

    break_hit = add_function_call(scan, "/Script/Engine.GameplayStatics:BreakHitResult", 500, -520, "hit result")
    connect(trace.find_output_pin("OutHit"), break_hit.find_input_pin("Hit"), "trace hit")
    component = add_function_call(scan, "/Script/Engine.Actor:GetComponentByClass", 800, -450, "Interactable contract lookup")
    set_pin(component.find_input_pin("ComponentClass"), interactable_path, "Interactable component class")
    connect(break_hit.find_output_pin("HitActor"), component.find_self_pin(), "hit entity")
    valid = add_function_call(scan, "/Script/Engine.KismetSystemLibrary:IsValid", 1050, -220, "Interactable validity")
    connect(component.find_result_pin(), valid.find_input_pin("Object"), "Interactable validity target")
    component_branch = scan.add_branch_node()
    component_branch.set_node_pos(unreal.IntPoint(1280, -80))
    connect(hit_branch.find_then_pin(), component_branch.find_execute_pin(), "hit Interactable check")
    connect(valid.find_result_pin(), component_branch.find_condition_pin(), "valid Interactable")
    clear_focus_nodes(scan, component_branch.find_else_pin(), 1560, 260)

    availability = add_get(scan, "InteractionAvailable", 1520, -420, interactable_path)
    connect(component.find_result_pin(), availability.find_self_pin(), "focused availability source")
    availability_branch = scan.add_branch_node()
    availability_branch.set_node_pos(unreal.IntPoint(1560, -80))
    connect(component_branch.find_then_pin(), availability_branch.find_execute_pin(), "Interactable availability check")
    connect(availability.find_result_pin(), availability_branch.find_condition_pin(), "available Interactable")
    clear_focus_nodes(scan, availability_branch.find_else_pin(), 1840, 260)

    set_focus = add_set(scan, "CurrentFocus", 1840, -100)
    set_prompt = add_set(scan, "CurrentPrompt", 2120, -100)
    prompt = add_get(scan, "InteractionPrompt", 1820, -400, interactable_path)
    connect(component.find_result_pin(), member_value_pin(set_focus, "CurrentFocus"), "focused Interactable")
    connect(component.find_result_pin(), prompt.find_self_pin(), "focused prompt source")
    connect(prompt.find_result_pin(), member_value_pin(set_prompt, "CurrentPrompt"), "focused prompt")
    connect(availability_branch.find_then_pin(), set_focus.find_execute_pin(), "acquire Interaction Focus")
    connect(set_focus.find_then_pin(), set_prompt.find_execute_pin(), "present Interaction Prompt")
    scan.set_function_is_public()

    request = unreal.BlueprintGraphEditor.create_and_edit_function_graph(blueprint, "TryInteract")
    request_entry = request.find_graph_entry_pin()
    focus = add_get(request, "CurrentFocus", -420, -180)
    focus_valid = add_function_call(request, "/Script/Engine.KismetSystemLibrary:IsValid", -180, -120, "Interaction Focus validity")
    connect(focus.find_result_pin(), focus_valid.find_input_pin("Object"), "focused Interactable validity")
    request_branch = request.add_branch_node()
    request_branch.set_node_pos(unreal.IntPoint(60, 0))
    connect(request_entry, request_branch.find_execute_pin(), "TryInteract entry")
    connect(focus_valid.find_result_pin(), request_branch.find_condition_pin(), "valid Interaction Focus")
    request_available = add_get(request, "InteractionAvailable", 300, -180, interactable_path)
    connect(focus.find_result_pin(), request_available.find_self_pin(), "focused availability source")
    available_branch = request.add_branch_node()
    available_branch.set_node_pos(unreal.IntPoint(520, 0))
    connect(request_branch.find_then_pin(), available_branch.find_execute_pin(), "focused Interaction")
    connect(request_available.find_result_pin(), available_branch.find_condition_pin(), "available focused Interaction")
    invoke = add_function_call(request, f"{interactable_path}:RequestInteraction", 800, 0, "generic Interaction request")
    connect(available_branch.find_then_pin(), invoke.find_execute_pin(), "available Interaction dispatch")
    connect(focus.find_result_pin(), invoke.find_self_pin(), "focused Interactable request target")
    request.set_function_is_public()

    compile_and_save(blueprint)
    return blueprint


def configure_player_interaction(player_blueprint, interaction_blueprint):
    component = add_component(player_blueprint, interaction_blueprint.generated_class(), "Interaction")
    unreal.BlueprintEditorLibrary.compile_blueprint(player_blueprint)
    graph = unreal.BlueprintGraphEditor.get_graph_editor_by_name(player_blueprint, "EventGraph")
    interaction_path = class_path(interaction_blueprint.generated_class())

    tick = unreal.BlueprintEditorLibrary.add_event_override(
        player_blueprint, "ReceiveTick", unreal.IntPoint(-700, 900)
    )
    require(tick is not None, "Could not add Player Tick")
    get_interaction = add_get(graph, "Interaction", -420, 980)
    scan = add_function_call(graph, f"{interaction_path}:ScanForInteractionFocus", -120, 900, "Interaction scan")
    connect(tick.find_then_pin(), scan.find_execute_pin(), "Player Tick to Interaction scan")
    connect(get_interaction.find_result_pin(), scan.find_self_pin(), "Player-owned Interaction scanner")

    input_node = graph.create_node_from_name(
        "Input|ActionEvents|Interact", unreal.Vector2D(-700.0, 1200.0), []
    )
    require(input_node is not None, "Could not create the Interact input event")
    get_for_input = add_get(graph, "Interaction", -420, 1280)
    request = add_function_call(graph, f"{interaction_path}:TryInteract", -120, 1200, "Interaction input")
    connect(input_node.find_output_pin("Pressed"), request.find_execute_pin(), "E press to Interaction")
    connect(get_for_input.find_result_pin(), request.find_self_pin(), "Player-owned Interaction input")
    return component


def external_set(graph, owner_node, variable_name, owner_path, value, x, y):
    node = add_set(graph, variable_name, x, y, owner_path)
    connect(owner_node.find_result_pin(), node.find_self_pin(), f"{variable_name} owner")
    set_pin(member_value_pin(node, variable_name), value, variable_name)
    return node


def create_door(interactable_blueprint, door_interactable_blueprint):
    delete_asset_if_present(DOOR_ASSET)
    blueprint = unreal.BlueprintEditorLibrary.create_blueprint_asset_with_parent(
        DOOR_ASSET, unreal.Actor
    )
    require(blueprint is not None, "Could not create BP_Door")
    hinge, hinge_handle = add_component_with_handle(
        blueprint, unreal.SceneComponent, "Hinge"
    )
    leaf, _ = add_component_with_handle(
        blueprint, unreal.StaticMeshComponent, "DoorLeaf", hinge_handle
    )
    interactable = add_component(blueprint, door_interactable_blueprint.generated_class(), "Interactable")
    interaction_zone = add_component(blueprint, unreal.BoxComponent, "InteractionZone")

    event_graph = unreal.BlueprintGraphEditor.get_graph_editor_by_name(blueprint, "EventGraph")
    require(event_graph.add_member_variable("IsOpen", unreal.BlueprintEditorLibrary.get_basic_type_by_name("bool"), "false"), "Could not add Door state")
    require(event_graph.add_member_variable("IsMoving", unreal.BlueprintEditorLibrary.get_basic_type_by_name("bool"), "false"), "Could not add Door motion state")
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)

    cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
    require(leaf is not None and cube is not None, "Could not configure the Door leaf")
    hinge.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    hinge.set_editor_property("relative_location", unreal.Vector(0.0, 50.0, 0.0))
    leaf.set_static_mesh(cube)
    leaf.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    leaf.set_editor_property("relative_location", unreal.Vector(0.0, -50.0, 0.0))
    leaf.set_relative_scale3d(unreal.Vector(0.12, 1.0, 2.1))
    interaction_zone.set_box_extent(unreal.Vector(20.0, 70.0, 105.0), False)

    graph = unreal.BlueprintGraphEditor.get_graph_editor_by_name(blueprint, "EventGraph")
    begin_play = unreal.BlueprintEditorLibrary.add_event_override(
        blueprint, "ReceiveBeginPlay", unreal.IntPoint(-1160, -620)
    )
    require(begin_play is not None, "Could not add Door BeginPlay")
    begin_contract = add_get(graph, "Interactable", -900, -500)
    begin_zone = add_get(graph, "InteractionZone", -900, -780)
    zone_collision = add_function_call(
        graph,
        "/Script/Engine.PrimitiveComponent:SetCollisionEnabled",
        -680,
        -860,
        "Interaction zone query collision",
    )
    set_pin(
        zone_collision.find_input_pin("NewType"),
        "QueryOnly",
        "Interaction zone collision",
    )
    connect(
        begin_zone.find_result_pin(),
        zone_collision.find_self_pin(),
        "Interaction zone collision target",
    )
    zone_ignore = add_function_call(
        graph,
        "/Script/Engine.PrimitiveComponent:SetCollisionResponseToAllChannels",
        -420,
        -860,
        "Interaction zone ignored channels",
    )
    set_pin(
        zone_ignore.find_input_pin("NewResponse"),
        "ECR_Ignore",
        "Interaction zone ignored channels",
    )
    connect(
        begin_zone.find_result_pin(),
        zone_ignore.find_self_pin(),
        "Interaction zone ignore target",
    )
    zone_visibility = add_function_call(
        graph,
        "/Script/Engine.PrimitiveComponent:SetCollisionResponseToChannel",
        -160,
        -860,
        "Interaction zone Visibility response",
    )
    set_pin(
        zone_visibility.find_input_pin("Channel"),
        "ECC_Visibility",
        "Interaction zone Visibility channel",
    )
    set_pin(
        zone_visibility.find_input_pin("NewResponse"),
        "ECR_Block",
        "Interaction zone Visibility response",
    )
    connect(
        begin_zone.find_result_pin(),
        zone_visibility.find_self_pin(),
        "Interaction zone Visibility target",
    )
    begin_prompt = external_set(
        graph,
        begin_contract,
        "InteractionPrompt",
        class_path(interactable_blueprint.generated_class()),
        "E — Open",
        -600,
        -620,
    )
    begin_available = external_set(
        graph,
        begin_contract,
        "InteractionAvailable",
        class_path(interactable_blueprint.generated_class()),
        "true",
        -320,
        -620,
    )
    connect(begin_play.find_then_pin(), zone_collision.find_execute_pin(), "initial Interaction zone")
    connect(zone_collision.find_then_pin(), zone_ignore.find_execute_pin(), "ignore non-Interaction channels")
    connect(zone_ignore.find_then_pin(), zone_visibility.find_execute_pin(), "block Interaction Visibility trace")
    connect(zone_visibility.find_then_pin(), begin_prompt.find_execute_pin(), "initial Door prompt")
    connect(begin_prompt.find_then_pin(), begin_available.find_execute_pin(), "initial Door availability")
    bind_request = graph.create_node_from_name(
        "Default|BindEventtoInteractionRequested", unreal.Vector2D(0.0, -620.0), []
    )
    require(bind_request is not None, "Could not bind the Door Interaction dispatcher")
    handle_request = graph.add_custom_event_node("HandleInteractionRequest")
    require(handle_request is not None, "Could not add the Door Interaction handler")
    handle_request.set_node_pos(unreal.IntPoint(-900, 0))
    connect(begin_available.find_then_pin(), bind_request.find_execute_pin(), "bind Door Interaction behavior")
    connect(begin_contract.find_result_pin(), bind_request.find_self_pin(), "Door dispatcher source")
    connect(handle_request.find_output_pin("OutputDelegate"), bind_request.find_input_pin("Delegate"), "Door Interaction handler")

    moving = add_get(graph, "IsMoving", -900, 180)
    moving_branch = graph.add_branch_node()
    moving_branch.set_node_pos(unreal.IntPoint(-380, 0))
    connect(handle_request.find_output_pin("then"), moving_branch.find_execute_pin(), "Door Interaction request")
    connect(moving.find_result_pin(), moving_branch.find_condition_pin(), "Door motion guard")

    open_state = add_get(graph, "IsOpen", -420, 180)
    open_branch = graph.add_branch_node()
    open_branch.set_node_pos(unreal.IntPoint(-340, 0))
    connect(moving_branch.find_else_pin(), open_branch.find_execute_pin(), "stationary Door request")
    connect(open_state.find_result_pin(), open_branch.find_condition_pin(), "Door state toggle")

    leaf_get_open = add_get(graph, "DoorLeaf", -80, -420)
    hinge_get_open = add_get(graph, "Hinge", 780, -240)
    contract_get_open = add_get(graph, "Interactable", -80, -260)
    set_moving_open = add_set(graph, "IsMoving", -40, 40)
    set_pin(member_value_pin(set_moving_open, "IsMoving"), "true", "opening state")
    unavailable_open = external_set(graph, contract_get_open, "InteractionAvailable", class_path(interactable_blueprint.generated_class()), "false", 220, 40)
    collision_open = add_function_call(graph, "/Script/Engine.PrimitiveComponent:SetCollisionEnabled", 500, 40, "opening collision")
    set_pin(collision_open.find_input_pin("NewType"), "QueryOnly", "opening Door collision")
    connect(leaf_get_open.find_result_pin(), collision_open.find_self_pin(), "opening Door leaf")
    pawn_ignore_open = add_function_call(graph, "/Script/Engine.PrimitiveComponent:SetCollisionResponseToChannel", 760, 40, "opening Pawn response")
    set_pin(pawn_ignore_open.find_input_pin("Channel"), "ECC_Pawn", "opening Pawn channel")
    set_pin(pawn_ignore_open.find_input_pin("NewResponse"), "ECR_Ignore", "opening Pawn response")
    connect(leaf_get_open.find_result_pin(), pawn_ignore_open.find_self_pin(), "opening Door response leaf")
    move_open = add_function_call(graph, "/Script/Engine.KismetSystemLibrary:MoveComponentTo", 1040, 40, "eased Door opening")
    connect(hinge_get_open.find_result_pin(), move_open.find_input_pin("Component"), "opening Hinge")
    set_pin(move_open.find_input_pin("TargetRelativeLocation"), "(X=0.0,Y=50.0,Z=0.0)", "opening Hinge location")
    set_pin(move_open.find_input_pin("TargetRelativeRotation"), "0, 90, 0", "opening rotation")
    set_pin(move_open.find_input_pin("bEaseOut"), "true", "opening ease out")
    set_pin(move_open.find_input_pin("bEaseIn"), "true", "opening ease in")
    set_pin(move_open.find_input_pin("OverTime"), "0.75", "opening duration")
    set_pin(move_open.find_input_pin("bForceShortestRotationPath"), "true", "opening rotation path")
    opened = add_set(graph, "IsOpen", 1360, 40)
    set_pin(member_value_pin(opened, "IsOpen"), "true", "open Door state")
    prompt_close = external_set(graph, contract_get_open, "InteractionPrompt", class_path(interactable_blueprint.generated_class()), "E — Close", 1620, 40)
    available_close = external_set(graph, contract_get_open, "InteractionAvailable", class_path(interactable_blueprint.generated_class()), "true", 1880, 40)
    stopped_open = add_set(graph, "IsMoving", 2140, 40)
    set_pin(member_value_pin(stopped_open, "IsMoving"), "false", "completed opening state")
    for source, target, description in [
        (open_branch.find_else_pin(), set_moving_open.find_execute_pin(), "begin opening"),
        (set_moving_open.find_then_pin(), unavailable_open.find_execute_pin(), "suspend opening Interaction"),
        (unavailable_open.find_then_pin(), collision_open.find_execute_pin(), "disable opening obstruction"),
        (collision_open.find_then_pin(), pawn_ignore_open.find_execute_pin(), "ignore Pawn while opening"),
        (pawn_ignore_open.find_then_pin(), move_open.find_input_pin("Move"), "animate opening"),
        (move_open.find_then_pin(), opened.find_execute_pin(), "complete open state"),
        (opened.find_then_pin(), prompt_close.find_execute_pin(), "present close prompt"),
        (prompt_close.find_then_pin(), available_close.find_execute_pin(), "restore open Interaction"),
        (available_close.find_then_pin(), stopped_open.find_execute_pin(), "finish opening"),
    ]:
        connect(source, target, description)

    leaf_get_close = add_get(graph, "DoorLeaf", -80, 500)
    hinge_get_close = add_get(graph, "Hinge", 780, 580)
    contract_get_close = add_get(graph, "Interactable", -80, 660)
    set_moving_close = add_set(graph, "IsMoving", -40, 860)
    set_pin(member_value_pin(set_moving_close, "IsMoving"), "true", "closing state")
    unavailable_close = external_set(graph, contract_get_close, "InteractionAvailable", class_path(interactable_blueprint.generated_class()), "false", 220, 860)
    collision_closing = add_function_call(graph, "/Script/Engine.PrimitiveComponent:SetCollisionEnabled", 500, 860, "closing collision")
    set_pin(collision_closing.find_input_pin("NewType"), "QueryOnly", "closing Door collision")
    connect(leaf_get_close.find_result_pin(), collision_closing.find_self_pin(), "closing Door leaf")
    pawn_ignore_close = add_function_call(graph, "/Script/Engine.PrimitiveComponent:SetCollisionResponseToChannel", 760, 860, "closing Pawn response")
    set_pin(pawn_ignore_close.find_input_pin("Channel"), "ECC_Pawn", "closing Pawn channel")
    set_pin(pawn_ignore_close.find_input_pin("NewResponse"), "ECR_Ignore", "closing Pawn response")
    connect(leaf_get_close.find_result_pin(), pawn_ignore_close.find_self_pin(), "closing Door response leaf")
    move_close = add_function_call(graph, "/Script/Engine.KismetSystemLibrary:MoveComponentTo", 1040, 860, "eased Door closing")
    connect(hinge_get_close.find_result_pin(), move_close.find_input_pin("Component"), "closing Hinge")
    set_pin(move_close.find_input_pin("TargetRelativeLocation"), "(X=0.0,Y=50.0,Z=0.0)", "closing Hinge location")
    set_pin(move_close.find_input_pin("TargetRelativeRotation"), "0, 0, 0", "closing rotation")
    set_pin(move_close.find_input_pin("bEaseOut"), "true", "closing ease out")
    set_pin(move_close.find_input_pin("bEaseIn"), "true", "closing ease in")
    set_pin(move_close.find_input_pin("OverTime"), "0.75", "closing duration")
    set_pin(move_close.find_input_pin("bForceShortestRotationPath"), "true", "closing rotation path")
    closed = add_set(graph, "IsOpen", 1360, 860)
    set_pin(member_value_pin(closed, "IsOpen"), "false", "closed Door state")
    collision_closed = add_function_call(graph, "/Script/Engine.PrimitiveComponent:SetCollisionEnabled", 1620, 860, "closed collision")
    set_pin(collision_closed.find_input_pin("NewType"), "QueryAndPhysics", "closed Door collision")
    connect(leaf_get_close.find_result_pin(), collision_closed.find_self_pin(), "closed Door leaf")
    pawn_block_closed = add_function_call(graph, "/Script/Engine.PrimitiveComponent:SetCollisionResponseToChannel", 1880, 860, "closed Pawn response")
    set_pin(pawn_block_closed.find_input_pin("Channel"), "ECC_Pawn", "closed Pawn channel")
    set_pin(pawn_block_closed.find_input_pin("NewResponse"), "ECR_Block", "closed Pawn response")
    connect(leaf_get_close.find_result_pin(), pawn_block_closed.find_self_pin(), "closed Door response leaf")
    prompt_open = external_set(graph, contract_get_close, "InteractionPrompt", class_path(interactable_blueprint.generated_class()), "E — Open", 2140, 860)
    available_open_again = external_set(graph, contract_get_close, "InteractionAvailable", class_path(interactable_blueprint.generated_class()), "true", 2400, 860)
    stopped_close = add_set(graph, "IsMoving", 2660, 860)
    set_pin(member_value_pin(stopped_close, "IsMoving"), "false", "completed closing state")
    for source, target, description in [
        (open_branch.find_then_pin(), set_moving_close.find_execute_pin(), "begin closing"),
        (set_moving_close.find_then_pin(), unavailable_close.find_execute_pin(), "suspend closing Interaction"),
        (unavailable_close.find_then_pin(), collision_closing.find_execute_pin(), "keep closing passage clear"),
        (collision_closing.find_then_pin(), pawn_ignore_close.find_execute_pin(), "ignore Pawn while closing"),
        (pawn_ignore_close.find_then_pin(), move_close.find_input_pin("Move"), "animate closing"),
        (move_close.find_then_pin(), closed.find_execute_pin(), "complete closed state"),
        (closed.find_then_pin(), collision_closed.find_execute_pin(), "restore closed obstruction"),
        (collision_closed.find_then_pin(), pawn_block_closed.find_execute_pin(), "restore closed Pawn block"),
        (pawn_block_closed.find_then_pin(), prompt_open.find_execute_pin(), "present open prompt"),
        (prompt_open.find_then_pin(), available_open_again.find_execute_pin(), "restore closed Interaction"),
        (available_open_again.find_then_pin(), stopped_close.find_execute_pin(), "finish closing"),
    ]:
        connect(source, target, description)

    compile_and_save(blueprint)
    return blueprint


def create_interaction_hud(interaction_blueprint):
    delete_asset_if_present(HUD_ASSET)
    blueprint = unreal.BlueprintEditorLibrary.create_blueprint_asset_with_parent(HUD_ASSET, unreal.HUD)
    require(blueprint is not None, "Could not create BP_InteractionHUD")
    graph = unreal.BlueprintGraphEditor.get_graph_editor_by_name(blueprint, "EventGraph")
    draw = unreal.BlueprintEditorLibrary.add_event_override(
        blueprint, "ReceiveDrawHUD", unreal.IntPoint(-900, 0)
    )
    require(draw is not None, "Could not add HUD draw event")

    dot = add_function_call(graph, "/Script/Engine.HUD:DrawText", -560, 0, "centre dot")
    set_pin(dot.find_input_pin("Text"), "·", "centre dot text")
    set_pin(dot.find_input_pin("TextColor"), "(R=0.65,G=0.65,B=0.65,A=0.55)", "centre dot colour")
    set_pin(dot.find_input_pin("ScreenX"), "1278.0", "centre dot X")
    set_pin(dot.find_input_pin("ScreenY"), "710.0", "centre dot Y")
    set_pin(dot.find_input_pin("Scale"), "1.25", "centre dot scale")
    connect(draw.find_then_pin(), dot.find_execute_pin(), "HUD centre dot")

    pawn = add_function_call(graph, "/Script/Engine.GameplayStatics:GetPlayerPawn", -620, -400, "HUD Player")
    set_pin(pawn.find_input_pin("PlayerIndex"), "0", "HUD player index")
    component = add_function_call(graph, "/Script/Engine.Actor:GetComponentByClass", -320, -400, "HUD Interaction component")
    set_pin(component.find_input_pin("ComponentClass"), class_path(interaction_blueprint.generated_class()), "HUD Interaction class")
    connect(pawn.find_result_pin(), component.find_self_pin(), "HUD Player component lookup")
    focus = add_get(graph, "CurrentFocus", 0, -400, class_path(interaction_blueprint.generated_class()))
    prompt = add_get(graph, "CurrentPrompt", 0, -260, class_path(interaction_blueprint.generated_class()))
    connect(component.find_result_pin(), focus.find_self_pin(), "HUD focus source")
    connect(component.find_result_pin(), prompt.find_self_pin(), "HUD prompt source")
    valid = add_function_call(graph, "/Script/Engine.KismetSystemLibrary:IsValid", 260, -320, "HUD focus validity")
    connect(focus.find_result_pin(), valid.find_input_pin("Object"), "HUD current focus")
    branch = graph.add_branch_node()
    branch.set_node_pos(unreal.IntPoint(500, 0))
    connect(dot.find_then_pin(), branch.find_execute_pin(), "prompt decision")
    connect(valid.find_result_pin(), branch.find_condition_pin(), "visible prompt focus")

    backing = add_function_call(graph, "/Script/Engine.HUD:DrawRect", 780, 0, "Interaction Prompt backing")
    set_pin(backing.find_input_pin("RectColor"), "(R=0.03,G=0.03,B=0.03,A=0.72)", "prompt backing colour")
    set_pin(backing.find_input_pin("ScreenX"), "1040.0", "prompt backing X")
    set_pin(backing.find_input_pin("ScreenY"), "1240.0", "prompt backing Y")
    set_pin(backing.find_input_pin("ScreenW"), "480.0", "prompt backing width")
    set_pin(backing.find_input_pin("ScreenH"), "64.0", "prompt backing height")
    prompt_text = add_function_call(graph, "/Script/Engine.HUD:DrawText", 1060, 0, "Interaction Prompt text")
    connect(prompt.find_result_pin(), prompt_text.find_input_pin("Text"), "contextual Interaction Prompt")
    set_pin(prompt_text.find_input_pin("TextColor"), "(R=0.92,G=0.92,B=0.92,A=1.0)", "prompt text colour")
    set_pin(prompt_text.find_input_pin("ScreenX"), "1160.0", "prompt text X")
    set_pin(prompt_text.find_input_pin("ScreenY"), "1256.0", "prompt text Y")
    connect(branch.find_then_pin(), backing.find_execute_pin(), "draw prompt backing")
    connect(backing.find_then_pin(), prompt_text.find_execute_pin(), "draw prompt text")

    compile_and_save(blueprint)
    return blueprint


def create_interaction_test_target(interactable_blueprint):
    delete_asset_if_present(TEST_INTERACTABLE_ASSET)
    blueprint = unreal.BlueprintEditorLibrary.create_blueprint_asset_with_parent(
        TEST_INTERACTABLE_ASSET, unreal.StaticMeshActor
    )
    require(blueprint is not None, "Could not create BP_InteractionTestTarget")
    add_component(blueprint, interactable_blueprint.generated_class(), "Interactable")
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)

    defaults = unreal.get_default_object(blueprint.generated_class())
    mesh = defaults.get_component_by_class(unreal.StaticMeshComponent)
    cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
    require(mesh is not None and cube is not None, "Could not configure the Interaction test target")
    mesh.set_static_mesh(cube)
    mesh.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
    mesh.set_relative_scale3d(unreal.Vector(0.3, 0.3, 0.3))
    compile_and_save(blueprint)
    return blueprint


def create_interaction_assets():
    interactable = create_interactable_component()
    save_blueprint(interactable)
    door_interactable = create_door_interactable_component(interactable)
    save_blueprint(door_interactable)
    interaction = create_interaction_component(interactable)
    save_blueprint(interaction)
    door = create_door(interactable, door_interactable)
    save_blueprint(door)
    hud = create_interaction_hud(interaction)
    save_blueprint(hud)
    test_target = create_interaction_test_target(interactable)
    save_blueprint(test_target)
    return interactable, interaction, door, hud, test_target
