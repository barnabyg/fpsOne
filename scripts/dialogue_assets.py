"""Project-authored proxy NPCs and the shared T03 dialogue presentation."""

import unreal

from interaction_assets import (
    add_component, add_function_call, add_get, add_set,
    class_path, clear_focus_nodes, compile_and_save, connect, member_value_pin, require,
    require_asset_absent, save_blueprint, set_pin,
)

NPC_ASSET = "/Game/Blueprints/BP_DialogueNPC"
NPC_INTERACTABLE_ASSET = "/Game/Blueprints/BPC_DialogueInteractable"
PANEL_ASSET = "/Game/Blueprints/BP_InteractionHUD"
DIALOGUE_ASSET_PATHS = (NPC_ASSET, NPC_INTERACTABLE_ASSET)


def cast_object(graph, source, blueprint, execution):
    suffix = "CastTo" + blueprint.get_name()
    choices = [name for name in graph.list_available_nodes([]) if name.endswith(suffix)]
    require(len(choices) == 1, f"Could not resolve {suffix}: {choices}")
    node = graph.create_node_from_name(choices[0], unreal.Vector2D(-300, 0), [])
    require(node is not None, suffix)
    connect(source, node.find_input_pin("Object"), suffix + " object")
    connect(execution, node.find_execute_pin(), suffix)
    outputs = unreal.BlueprintEditorLibrary.list_output_pins(node)
    values = [pin for pin in outputs if str(pin.get_pin_name()).startswith("As")]
    require(len(values) == 1, f"Unexpected cast outputs: {[str(pin.get_pin_name()) for pin in outputs]}")
    return values[0], node.find_then_pin()


def create_presentation():
    """One Canvas HUD exposes exactly the presentation values its draw graph consumes."""
    require_asset_absent(PANEL_ASSET)
    panel = unreal.BlueprintEditorLibrary.create_blueprint_asset_with_parent(PANEL_ASSET, unreal.HUD)
    graph = unreal.BlueprintGraphEditor.create_and_edit_function_graph(panel, "Present")
    execution = graph.find_graph_entry_pin()
    for index, (name, kind, default) in enumerate((
        ("DialogueVisible", "bool", "false"), ("DialogueText", "text", ""),
        ("PromptText", "text", ""),
    )):
        pin_type = unreal.BlueprintEditorLibrary.get_basic_type_by_name(kind)
        require(graph.add_member_variable(name, pin_type, default), name)
        value = graph.add_graph_input_parameter(name, pin_type)
        setter = add_set(graph, name, index * 300, 0)
        connect(value, member_value_pin(setter, name), name)
        connect(execution, setter.find_execute_pin(), name)
        execution = setter.find_then_pin()
    graph.set_function_is_public()
    compile_and_save(panel)
    graph = unreal.BlueprintGraphEditor.get_graph_editor_by_name(panel, "EventGraph")
    draw = unreal.BlueprintEditorLibrary.add_event_override(panel, "ReceiveDrawHUD", unreal.IntPoint(-1200, 0))
    active = add_get(graph, "DialogueVisible", -1000, -200)
    branch = graph.add_branch_node()
    connect(draw.find_then_pin(), branch.find_execute_pin(), "HUD presentation mode")
    connect(active.find_result_pin(), branch.find_condition_pin(), "visible dialogue")

    def coordinate(size_pin, ratio, offset, x, y):
        # Convert before connecting a promotable arithmetic node: an integer
        # viewport pin otherwise changes its fractional multiplier to an integer.
        to_real = add_function_call(graph, "/Script/Engine.KismetMathLibrary:Conv_IntToDouble", x - 200, y, "fractional viewport size")
        connect(size_pin, to_real.find_input_pin("InInt"), "integer viewport size")
        multiply = add_function_call(graph, "/Script/Engine.KismetMathLibrary:Multiply_DoubleDouble", x, y, "viewport proportion")
        connect(to_real.find_result_pin(), multiply.find_input_pin("A"), "viewport size")
        set_pin(multiply.find_input_pin("B"), ratio, "viewport ratio")
        add = add_function_call(graph, "/Script/Engine.KismetMathLibrary:Add_DoubleDouble", x + 200, y, "viewport offset")
        connect(multiply.find_result_pin(), add.find_input_pin("A"), "relative screen position")
        set_pin(add.find_input_pin("B"), offset, "screen offset")
        return add.find_result_pin()

    def draw_panel(execution, text_name, y, width_ratio, height, bottom):
        backing = add_function_call(graph, "/Script/Engine.HUD:DrawRect", 200, y, "charcoal panel")
        set_pin(backing.find_input_pin("RectColor"), "(R=0.03,G=0.03,B=0.03,A=0.82)", "panel colour")
        connect(coordinate(draw.find_output_pin("SizeX"), (1-width_ratio)/2, 0, -700, y-300), backing.find_input_pin("ScreenX"), "panel X")
        connect(coordinate(draw.find_output_pin("SizeY"), 1, -bottom-height, -700, y-180), backing.find_input_pin("ScreenY"), "panel Y")
        connect(coordinate(draw.find_output_pin("SizeX"), width_ratio, 0, -700, y-60), backing.find_input_pin("ScreenW"), "panel width")
        set_pin(backing.find_input_pin("ScreenH"), height, "panel height")
        text = add_function_call(graph, "/Script/Engine.HUD:DrawText", 500, y, "speaker-labelled panel text")
        value = add_get(graph, text_name, 200, y-180)
        connect(value.find_result_pin(), text.find_input_pin("Text"), "panel text")
        set_pin(text.find_input_pin("TextColor"), "(R=0.92,G=0.92,B=0.92,A=1.0)", "text colour")
        set_pin(text.find_input_pin("Scale"), "1.4", "text scale")
        connect(coordinate(draw.find_output_pin("SizeX"), (1-width_ratio)/2, 24, 0, y-300), text.find_input_pin("ScreenX"), "text X")
        connect(coordinate(draw.find_output_pin("SizeY"), 1, -bottom-height+24, 0, y-150), text.find_input_pin("ScreenY"), "text Y")
        connect(execution, backing.find_execute_pin(), "draw panel")
        connect(backing.find_then_pin(), text.find_execute_pin(), "draw content")
        return text.find_then_pin()

    draw_panel(branch.find_then_pin(), "DialogueText", 0, 0.8, 120, 48)
    dot = add_function_call(graph, "/Script/Engine.HUD:DrawText", -500, 700, "centre dot")
    set_pin(dot.find_input_pin("Text"), "·", "centre dot")
    set_pin(dot.find_input_pin("TextColor"), "(R=0.65,G=0.65,B=0.65,A=0.55)", "dot colour")
    connect(coordinate(draw.find_output_pin("SizeX"), 0.5, -2, -1000, 400), dot.find_input_pin("ScreenX"), "dot X")
    connect(coordinate(draw.find_output_pin("SizeY"), 0.5, -10, -1000, 530), dot.find_input_pin("ScreenY"), "dot Y")
    connect(branch.find_else_pin(), dot.find_execute_pin(), "exploration dot")
    prompt = add_get(graph, "PromptText", -500, 1000)
    empty = add_function_call(graph, "/Script/Engine.KismetTextLibrary:TextIsEmpty", -250, 1000, "empty prompt")
    connect(prompt.find_result_pin(), empty.find_input_pin("InText"), "prompt text")
    prompt_branch = graph.add_branch_node()
    connect(dot.find_then_pin(), prompt_branch.find_execute_pin(), "prompt decision")
    connect(empty.find_result_pin(), prompt_branch.find_condition_pin(), "prompt emptiness")
    draw_panel(prompt_branch.find_else_pin(), "PromptText", 1450, 0.25, 72, 110)
    compile_and_save(panel)
    save_blueprint(panel)
    return panel

def line_array_type():
    return unreal.BlueprintEditorLibrary.get_array_type(
        unreal.BlueprintEditorLibrary.get_basic_type_by_name("text")
    )


def configure_dialogue(interaction, panel):
    graph = unreal.BlueprintGraphEditor.get_graph_editor_by_name(interaction, "EventGraph")
    for name, kind, default in (
        ("DialogueActive", "bool", "false"), ("DialogueLine", "text", ""),
        ("DialogueIndex", "int", "0"),
    ):
        require(graph.add_member_variable(name, unreal.BlueprintEditorLibrary.get_basic_type_by_name(kind), default), name)
    require(graph.add_member_variable("DialogueLines", line_array_type()), "DialogueLines")
    actor_type = unreal.BlueprintEditorLibrary.get_object_reference_type(unreal.Actor)
    require(graph.add_member_variable("DialogueActor", actor_type), "DialogueActor")
    start = unreal.BlueprintGraphEditor.create_and_edit_function_graph(interaction, "StartDialogue")
    lines = start.add_graph_input_parameter("Lines", line_array_type())
    speaker = start.add_graph_input_parameter("Speaker", actor_type)
    refresh = unreal.BlueprintGraphEditor.create_and_edit_function_graph(interaction, "RefreshPresentation")
    advance = unreal.BlueprintGraphEditor.create_and_edit_function_graph(interaction, "AdvanceDialogue")
    end = unreal.BlueprintGraphEditor.create_and_edit_function_graph(interaction, "EndDialogue")
    suspend = unreal.BlueprintGraphEditor.create_and_edit_function_graph(interaction, "SuspendDialogueControls")
    restore = unreal.BlueprintGraphEditor.create_and_edit_function_graph(interaction, "RestoreDialogueControls")
    for name in ("ViewYawMin", "ViewYawMax", "ViewPitchMin", "ViewPitchMax"):
        require(graph.add_member_variable("Saved" + name, unreal.BlueprintEditorLibrary.get_basic_type_by_name("float")), name)
    compile_and_save(interaction)
    path = class_path(interaction.generated_class())

    controller = add_function_call(refresh, "/Script/Engine.GameplayStatics:GetPlayerController", -700, -200, "HUD player")
    hud = add_function_call(refresh, "/Script/Engine.PlayerController:GetHUD", -500, -200, "shared HUD")
    connect(controller.find_result_pin(), hud.find_self_pin(), "HUD owner")
    hud_value, hud_execution = cast_object(refresh, hud.find_result_pin(), panel, refresh.find_graph_entry_pin())
    present = add_function_call(refresh, f"{class_path(panel.generated_class())}:Present", 0, 0, "shared UI refresh")
    connect(hud_value, present.find_self_pin(), "UI refresh target")
    connect(hud_execution, present.find_execute_pin(), "refresh presentation")
    for variable, pin in (("DialogueActive", "DialogueVisible"), ("DialogueLine", "DialogueText"), ("CurrentPrompt", "PromptText")):
        getter = add_get(refresh, variable, -250, -200)
        connect(getter.find_result_pin(), present.find_input_pin(pin), variable)
    refresh.set_function_is_public()
    store_lines = add_set(start, "DialogueLines", 0, 0)
    connect(lines, member_value_pin(store_lines, "DialogueLines"), "NPC-owned lines")
    active = add_set(start, "DialogueActive", 300, 0)
    set_pin(member_value_pin(active, "DialogueActive"), "true", "dialogue active")
    first = add_function_call(start, "/Script/Engine.KismetArrayLibrary:Array_Get", 300, -200, "first dialogue line")
    connect(lines, first.find_input_pin("TargetArray"), "initial line array")
    set_pin(first.find_input_pin("Index"), "0", "initial line index")
    line = add_set(start, "DialogueLine", 600, 0)
    connect(first.find_output_pin("Item"), member_value_pin(line, "DialogueLine"), "initial line")
    show = add_function_call(start, f"{path}:RefreshPresentation", 900, 0, "show initial dialogue")
    # Repeated requests cannot restart an active exchange or read an empty array.
    is_active = add_get(start, "DialogueActive", -900, -200)
    active_branch = start.add_branch_node()
    connect(start.find_graph_entry_pin(), active_branch.find_execute_pin(), "dialogue start guard")
    connect(is_active.find_result_pin(), active_branch.find_condition_pin(), "existing exchange")
    length = add_function_call(start, "/Script/Engine.KismetArrayLibrary:Array_Length", -700, -200, "exchange length")
    connect(lines, length.find_input_pin("TargetArray"), "NPC line count")
    nonempty = add_function_call(start, "/Script/Engine.KismetMathLibrary:Greater_IntInt", -500, -200, "nonempty exchange")
    connect(length.find_result_pin(), nonempty.find_input_pin("A"), "line count")
    set_pin(nonempty.find_input_pin("B"), "0", "minimum exchange length")
    content_branch = start.add_branch_node()
    connect(active_branch.find_else_pin(), content_branch.find_execute_pin(), "idle dialogue request")
    connect(nonempty.find_result_pin(), content_branch.find_condition_pin(), "has dialogue content")
    reset_index = add_set(start, "DialogueIndex", -250, 0)
    set_pin(member_value_pin(reset_index, "DialogueIndex"), "0", "first line index")
    connect(content_branch.find_then_pin(), reset_index.find_execute_pin(), "reset exchange")
    connect(reset_index.find_then_pin(), store_lines.find_execute_pin(), "start dialogue")
    store_speaker = add_set(start, "DialogueActor", 150, 150)
    connect(speaker, member_value_pin(store_speaker, "DialogueActor"), "active dialogue occupant")
    connect(store_lines.find_then_pin(), store_speaker.find_execute_pin(), "remember occupant")
    connect(store_speaker.find_then_pin(), active.find_execute_pin(), "activate dialogue")
    connect(active.find_then_pin(), line.find_execute_pin(), "present initial line")
    suspend_call = add_function_call(start, f"{path}:SuspendDialogueControls", 800, 200, "suspend exploration")
    connect(line.find_then_pin(), suspend_call.find_execute_pin(), "pause dialogue controls")
    connect(suspend_call.find_then_pin(), show.find_execute_pin(), "show dialogue")
    start.set_function_is_public()

    execution = end.find_graph_entry_pin()
    clear_speaker = add_set(end, "DialogueActor", -300, 0)
    connect(execution, clear_speaker.find_execute_pin(), "release dialogue occupant")
    execution = clear_speaker.find_then_pin()
    for index, (name, value) in enumerate((("DialogueActive", "false"), ("DialogueLine", ""), ("DialogueIndex", "0"))):
        setter = add_set(end, name, index * 300, 0)
        set_pin(member_value_pin(setter, name), value, "reset " + name)
        connect(execution, setter.find_execute_pin(), "dismiss " + name)
        execution = setter.find_then_pin()
    empty_lines = add_function_call(end, "/Script/Engine.KismetArrayLibrary:Array_Clear", 900, 0, "release exchange content")
    stored_lines = add_get(end, "DialogueLines", 900, -200)
    connect(stored_lines.find_result_pin(), empty_lines.find_input_pin("TargetArray"), "exchange to release")
    connect(execution, empty_lines.find_execute_pin(), "release exchange content")
    end_refresh = add_function_call(end, f"{path}:RefreshPresentation", 1200, 0, "dismiss presentation")
    restore_call = add_function_call(end, f"{path}:RestoreDialogueControls", 1000, 200, "restore exploration")
    connect(empty_lines.find_then_pin(), restore_call.find_execute_pin(), "restore controls")
    connect(restore_call.find_then_pin(), end_refresh.find_execute_pin(), "refresh dismissed presentation")

    current = add_get(advance, "DialogueIndex", -600, -250)
    increment = add_function_call(advance, "/Script/Engine.KismetMathLibrary:Add_IntInt", -350, -250, "next dialogue line")
    connect(current.find_result_pin(), increment.find_input_pin("A"), "current line index")
    set_pin(increment.find_input_pin("B"), "1", "one line per E")
    next_index = add_set(advance, "DialogueIndex", -100, 0)
    connect(increment.find_result_pin(), member_value_pin(next_index, "DialogueIndex"), "advance index")
    connect(advance.find_graph_entry_pin(), next_index.find_execute_pin(), "advance dialogue")
    stored = add_get(advance, "DialogueLines", 0, -400)
    length = add_function_call(advance, "/Script/Engine.KismetArrayLibrary:Array_Length", 250, -400, "stored exchange length")
    connect(stored.find_result_pin(), length.find_input_pin("TargetArray"), "stored lines")
    index = add_get(advance, "DialogueIndex", 250, -200)
    remaining = add_function_call(advance, "/Script/Engine.KismetMathLibrary:Less_IntInt", 500, -200, "remaining dialogue")
    connect(index.find_result_pin(), remaining.find_input_pin("A"), "next index")
    connect(length.find_result_pin(), remaining.find_input_pin("B"), "exchange end")
    branch = advance.add_branch_node()
    connect(next_index.find_then_pin(), branch.find_execute_pin(), "line advancement decision")
    connect(remaining.find_result_pin(), branch.find_condition_pin(), "line remains")
    item = add_function_call(advance, "/Script/Engine.KismetArrayLibrary:Array_Get", 750, -200, "next line text")
    connect(stored.find_result_pin(), item.find_input_pin("TargetArray"), "exchange source")
    connect(index.find_result_pin(), item.find_input_pin("Index"), "next line")
    next_line = add_set(advance, "DialogueLine", 1000, 0)
    connect(item.find_output_pin("Item"), member_value_pin(next_line, "DialogueLine"), "next dialogue text")
    connect(branch.find_then_pin(), next_line.find_execute_pin(), "show next line")
    next_refresh = add_function_call(advance, f"{path}:RefreshPresentation", 1300, 0, "refresh next line")
    connect(next_line.find_then_pin(), next_refresh.find_execute_pin(), "present advanced line")
    finish = add_function_call(advance, f"{path}:EndDialogue", 1000, 350, "complete exchange")
    connect(branch.find_else_pin(), finish.find_execute_pin(), "dismiss after last line")

    request = unreal.BlueprintGraphEditor.get_graph_editor_by_name(interaction, "TryInteract")
    entry = request.find_graph_entry_pin()
    original = entry.list_connected_pins()[0]
    entry.break_pin_links()
    active = add_get(request, "DialogueActive", -900, -200)
    branch = request.add_branch_node()
    connect(entry, branch.find_execute_pin(), "contextual E routing")
    connect(active.find_result_pin(), branch.find_condition_pin(), "dialogue in progress")
    advance_call = add_function_call(request, f"{path}:AdvanceDialogue", -600, 400, "advance active exchange")
    connect(branch.find_then_pin(), advance_call.find_execute_pin(), "dialogue E input")
    connect(branch.find_else_pin(), original, "world E input")

    scan = unreal.BlueprintGraphEditor.get_graph_editor_by_name(interaction, "ScanForInteractionFocus")
    entry = scan.find_graph_entry_pin()
    original = entry.list_connected_pins()[0]
    entry.break_pin_links()
    active = add_get(scan, "DialogueActive", -1500, -200)
    branch = scan.add_branch_node()
    connect(entry, branch.find_execute_pin(), "scan suspension")
    connect(active.find_result_pin(), branch.find_condition_pin(), "dialogue scan guard")
    connect(branch.find_else_pin(), original, "exploration scan")
    clear_focus_nodes(scan, branch.find_then_pin(), -1200, 400)

    configure_control_graph(suspend, restoring=False)
    configure_control_graph(restore, restoring=True)
    compile_and_save(interaction)


def configure_control_graph(graph, restoring):
    controller = add_function_call(graph, "/Script/Engine.GameplayStatics:GetPlayerController", -900, -400, "dialogue controller")
    camera = add_function_call(graph, "/Script/Engine.GameplayStatics:GetPlayerCameraManager", -900, -600, "dialogue camera")
    ignore = add_function_call(graph, "/Script/Engine.Controller:SetIgnoreMoveInput", -600, 0, "dialogue movement input")
    connect(controller.find_result_pin(), ignore.find_self_pin(), "movement controller")
    set_pin(ignore.find_input_pin("bNewMoveInput"), "false" if restoring else "true", "movement suspension")
    connect(graph.find_graph_entry_pin(), ignore.find_execute_pin(), "movement input mode")
    execution = ignore.find_then_pin()
    if not restoring:
        pawn = add_function_call(graph, "/Script/Engine.GameplayStatics:GetPlayerPawn", -900, 200, "dialogue Player")
        movement = add_function_call(graph, "/Script/Engine.Pawn:GetMovementComponent", -650, 200, "Player movement")
        connect(pawn.find_result_pin(), movement.find_self_pin(), "Player movement owner")
        stop = add_function_call(graph, "/Script/Engine.MovementComponent:StopMovementImmediately", -350, 0, "stop existing velocity")
        connect(movement.find_result_pin(), stop.find_self_pin(), "movement to stop")
        connect(execution, stop.find_execute_pin(), "stop walking")
        consume = add_function_call(graph, "/Script/Engine.Pawn:ConsumeMovementInputVector", -100, 0, "clear pending walking input")
        connect(pawn.find_result_pin(), consume.find_self_pin(), "pending Player input")
        connect(stop.find_then_pin(), consume.find_execute_pin(), "consume pending input")
        execution = consume.find_then_pin()
        rotation = add_function_call(graph, "/Script/Engine.Controller:GetControlRotation", -350, -400, "dialogue starting view")
        connect(controller.find_result_pin(), rotation.find_self_pin(), "view controller")
        split = add_function_call(graph, "/Script/Engine.KismetMathLibrary:BreakRotator", -100, -400, "starting view axes")
        connect(rotation.find_result_pin(), split.find_input_pin("InRot"), "starting view rotation")
    camera_path = "/Script/Engine.PlayerCameraManager"
    for index, (name, axis, offset) in enumerate((
        ("ViewYawMin", "Yaw", -35), ("ViewYawMax", "Yaw", 35),
        ("ViewPitchMin", "Pitch", -20), ("ViewPitchMax", "Pitch", 20),
    )):
        x = 250 + index * 600
        if restoring:
            value = add_get(graph, "Saved" + name, x, -200).find_result_pin()
        else:
            previous = add_get(graph, name, x, -200, camera_path)
            connect(camera.find_result_pin(), previous.find_self_pin(), "prior camera limit")
            saved = add_set(graph, "Saved" + name, x, 0)
            connect(previous.find_result_pin(), member_value_pin(saved, "Saved" + name), "save original camera limit")
            connect(execution, saved.find_execute_pin(), "save " + name)
            execution = saved.find_then_pin()
            limited = add_function_call(graph, "/Script/Engine.KismetMathLibrary:Add_DoubleDouble", x, -400, "limited dialogue look")
            connect(split.find_output_pin(axis), limited.find_input_pin("A"), "starting " + axis)
            set_pin(limited.find_input_pin("B"), offset, "dialogue look range")
            value = limited.find_result_pin()
        setter = add_set(graph, name, x + 300, 0, camera_path)
        connect(camera.find_result_pin(), setter.find_self_pin(), "camera limit owner")
        connect(value, member_value_pin(setter, name), "camera limit")
        connect(execution, setter.find_execute_pin(), name)
        execution = setter.find_then_pin()
    if not restoring:
        clear_focus_nodes(graph, execution, 2800, 0)


def create_npc_assets(interactable, interaction):
    require_asset_absent(NPC_INTERACTABLE_ASSET)
    contract = unreal.BlueprintEditorLibrary.create_blueprint_asset_with_parent(
        NPC_INTERACTABLE_ASSET, interactable.generated_class()
    )
    compile_and_save(contract)
    unreal.get_default_object(contract.generated_class()).set_editor_property(
        "InteractionPrompt", unreal.Text("E — Talk")
    )
    save_blueprint(contract)

    require_asset_absent(NPC_ASSET)
    npc = unreal.BlueprintEditorLibrary.create_blueprint_asset_with_parent(NPC_ASSET, unreal.Character)
    add_component(npc, contract.generated_class(), "Interactable")
    graph = unreal.BlueprintGraphEditor.get_graph_editor_by_name(npc, "EventGraph")
    require(graph.add_member_variable("DialogueLines", line_array_type()), "Could not add NPC dialogue lines")
    unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(npc, "DialogueLines", True)
    body = add_component(npc, unreal.StaticMeshComponent, "ProxyBody")
    body.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cylinder.Cylinder"))
    body.set_relative_scale3d(unreal.Vector(0.5, 0.5, 1.15))
    body.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, -8.0))
    head = add_component(npc, unreal.StaticMeshComponent, "ProxyHead")
    head.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Sphere.Sphere"))
    head.set_relative_scale3d(unreal.Vector(0.38, 0.38, 0.38))
    head.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, 65.0))
    for mesh in (body, head):
        mesh.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    compile_and_save(npc)
    defaults = unreal.get_default_object(npc.generated_class())
    defaults.set_editor_property("tags", [unreal.Name("DialogueNPC")])
    capsule = defaults.get_component_by_class(unreal.CapsuleComponent)
    capsule.set_capsule_size(34.0, 90.0)
    capsule.set_collision_profile_name("BlockAllDynamic")
    save_blueprint(npc)

    override = unreal.BlueprintEditorLibrary.add_function_override(contract, "RequestInteraction")
    graph = unreal.BlueprintGraphEditor.get_graph_editor(override)
    for node in graph.list_all_nodes():
        if "Parent" in node.get_node_title():
            graph.remove_nodes([node])
    owner = add_function_call(graph, "/Script/Engine.ActorComponent:GetOwner", -700, -300, "NPC owner")
    npc_value, npc_execution = cast_object(graph, owner.find_result_pin(), npc, graph.find_graph_entry_pin())
    npc_lines = add_get(graph, "DialogueLines", -400, -300, class_path(npc.generated_class()))
    connect(npc_value, npc_lines.find_self_pin(), "NPC dialogue source")
    player = add_function_call(graph, "/Script/Engine.GameplayStatics:GetPlayerPawn", -700, -100, "interacting Player")
    component = add_function_call(graph, "/Script/Engine.Actor:GetComponentByClass", -400, -100, "player Interaction seam")
    connect(player.find_result_pin(), component.find_self_pin(), "player Interaction owner")
    set_pin(component.find_input_pin("ComponentClass"), class_path(interaction.generated_class()), "Interaction class")
    start = add_function_call(graph, f"{class_path(interaction.generated_class())}:StartDialogue", 0, 0, "begin NPC exchange")
    connect(component.find_result_pin(), start.find_self_pin(), "player Dialogue Interaction")
    connect(npc_lines.find_result_pin(), start.find_input_pin("Lines"), "NPC-owned exchange")
    connect(owner.find_result_pin(), start.find_input_pin("Speaker"), "dialogue occupant")
    connect(npc_execution, start.find_execute_pin(), "NPC request")
    compile_and_save(contract)
    save_blueprint(contract)
    return npc
