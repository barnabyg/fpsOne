"""Import the CC0 resident and attach presentation to the shared Dialogue NPC.

Runs only in the isolated regeneration project. Runtime remains Blueprint-only.
"""
from pathlib import Path
import sys
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from interaction_assets import (
    add_component, add_function_call, add_get, add_set, class_path,
    compile_and_save, connect, member_value_pin, require, save_blueprint, set_pin,
)
import room_a_assets as art

ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE = ROOT / 'SourceArt/Characters/NPC_A'
DEST = '/Game/Characters/NPC_A'
BLUEPRINT = '/Game/Blueprints/BP_NPC_A'


def import_fbx(name, skeleton=None):
    # Use the pinned legacy skeletal importer; the project remains Blueprint-only.
    unreal.SystemLibrary.execute_console_command(None, 'Interchange.FeatureFlags.Import.FBX 0')
    task = unreal.AssetImportTask()
    task.filename = str(SOURCE / (name + '.fbx'))
    task.destination_path = DEST
    task.destination_name = name
    task.automated = True
    task.save = True
    options = unreal.FbxImportUI()
    options.automated_import_should_detect_type = False
    options.import_materials = False
    options.import_textures = False
    options.create_physics_asset = False
    options.import_as_skeletal = True
    options.import_mesh = skeleton is None
    options.import_animations = skeleton is not None
    options.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH if skeleton is None else unreal.FBXImportType.FBXIT_ANIMATION
    if skeleton:
        options.skeleton = skeleton
        options.anim_sequence_import_data.set_editor_property('animation_length', unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
    else:
        options.skeletal_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    objects = task.get_objects()
    kind = unreal.SkeletalMesh if skeleton is None else unreal.AnimSequence
    result = [obj for obj in objects if isinstance(obj, kind)]
    require(len(result) == 1, f'Expected one imported {kind}: {objects}')
    return result[0]


def character_material(name, filename, roughness, masked=False, normal=None):
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_' + name, DEST + '/Materials', unreal.Material, unreal.MaterialFactoryNew())
    if masked:
        material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
        material.set_editor_property('two_sided', True)
        material.set_editor_property('opacity_mask_clip_value', 0.35)
    unreal.MaterialEditingLibrary.set_base_material_usage(material, unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH)
    for file, channel in ((filename, 'color'), (normal, 'normal')):
        if not file:
            continue
        imported = art.import_file(SOURCE / 'Textures' / file, DEST + '/Textures')
        texture = next(obj for obj in imported if isinstance(obj, unreal.Texture2D))
        if channel == 'normal':
            texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
            texture.set_editor_property('srgb', False)
            texture.set_editor_property('flip_green_channel', True)
        node = art.expression(material, unreal.MaterialExpressionTextureSample, texture=texture)
        if channel == 'normal':
            node.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        if name == 'Skin' and channel == 'color':
            # The core skin's bright albedo needs calibration under the apartment
            # sun. Avoid broad subsurface scattering that washes out the face.
            gain = art.expression(material, unreal.MaterialExpressionMultiply, const_b=0.72)
            unreal.MaterialEditingLibrary.connect_material_expressions(node, 'RGB', gain, 'A')
            unreal.MaterialEditingLibrary.connect_material_property(gain, '', unreal.MaterialProperty.MP_BASE_COLOR)
        else:
            unreal.MaterialEditingLibrary.connect_material_property(node, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR if channel == 'color' else unreal.MaterialProperty.MP_NORMAL)
        if channel == 'color' and masked:
            unreal.MaterialEditingLibrary.connect_material_property(node, 'A', unreal.MaterialProperty.MP_OPACITY_MASK)
    value = art.expression(material, unreal.MaterialExpressionConstant, r=roughness)
    unreal.MaterialEditingLibrary.connect_material_property(value, '', unreal.MaterialProperty.MP_ROUGHNESS)
    if name == 'Skin':
        specular = art.expression(material, unreal.MaterialExpressionConstant, r=0.25)
        unreal.MaterialEditingLibrary.connect_material_property(specular, '', unreal.MaterialProperty.MP_SPECULAR)
    unreal.MaterialEditingLibrary.recompile_material(material)
    return material


def add_presentation_graph(blueprint, idle, talk):
    construction = unreal.BlueprintGraphEditor.get_graph_editor_by_name(blueprint, 'UserConstructionScript')
    execution = construction.find_graph_entry_pin()
    for index, name in enumerate(('ProxyBody', 'ProxyHead')):
        proxy = add_get(construction, name, index * 350, -200)
        hide = add_function_call(construction, '/Script/Engine.SceneComponent:SetVisibility', index * 350, 0, 'replace inherited proxy art')
        connect(proxy.find_result_pin(), hide.find_self_pin(), 'proxy component')
        set_pin(hide.find_input_pin('bNewVisibility'), 'false', 'hide proxy')
        connect(execution, hide.find_execute_pin(), 'refined resident construction')
        execution = hide.find_then_pin()
    graph = unreal.BlueprintGraphEditor.get_graph_editor_by_name(blueprint, 'EventGraph')
    require(graph.add_member_variable('TalkPlaying', unreal.BlueprintEditorLibrary.get_basic_type_by_name('bool'), 'false'), 'TalkPlaying')
    require(graph.add_member_variable('TransitionPhase', unreal.BlueprintEditorLibrary.get_basic_type_by_name('float'), '0'), 'TransitionPhase')
    tick = unreal.BlueprintEditorLibrary.add_event_override(blueprint, 'ReceiveTick', unreal.IntPoint(-1200, 0))
    visual = add_get(graph, 'CharacterVisual', -1000, -200)
    player = add_function_call(graph, '/Script/Engine.GameplayStatics:GetPlayerPawn', -1400, -600, 'nearby Player')
    component = add_function_call(graph, '/Script/Engine.Actor:GetComponentByClass', -1100, -600, 'shared Interaction')
    connect(player.find_result_pin(), component.find_self_pin(), 'Interaction owner')
    interaction = unreal.load_asset('/Game/Blueprints/BPC_Interaction')
    set_pin(component.find_input_pin('ComponentClass'), class_path(interaction.generated_class()), 'Interaction component')
    valid = add_function_call(graph, '/Script/Engine.KismetSystemLibrary:IsValid', -800, -650, 'valid Player Interaction')
    connect(component.find_result_pin(), valid.find_input_pin('Object'), 'available Interaction')
    guard = graph.add_branch_node()
    connect(tick.find_then_pin(), guard.find_execute_pin(), 'presentation tick')
    connect(valid.find_result_pin(), guard.find_condition_pin(), 'Player ready')
    speaker = add_get(graph, 'DialogueActor', -750, -400, class_path(interaction.generated_class()))
    connect(component.find_result_pin(), speaker.find_self_pin(), 'active occupant')
    own = graph.create_node_from_name('Variables|Getareferencetoself', unreal.Vector2D(-800, -900), [])
    require(own, 'self reference')
    equal = add_function_call(graph, '/Script/Engine.KismetMathLibrary:EqualEqual_ObjectObject', -450, -400, 'this resident speaking')
    connect(speaker.find_result_pin(), equal.find_input_pin('A'), 'dialogue actor')
    connect(own.find_result_pin(), equal.find_input_pin('B'), 'this NPC')
    previous = add_get(graph, 'TalkPlaying', -450, -200)
    changed = add_function_call(graph, '/Script/Engine.KismetMathLibrary:NotEqual_BoolBool', -150, -200, 'animation transition')
    connect(equal.find_result_pin(), changed.find_input_pin('A'), 'current speaking state')
    connect(previous.find_result_pin(), changed.find_input_pin('B'), 'previous speaking state')
    # Both clips share the same pose outside the 1–4 second gesture. Finish a
    # raised arm before returning to idle, and retain the breathing/blink phase.
    phase = add_function_call(graph, '/Script/Engine.SkeletalMeshComponent:GetPosition', -1050, -1200, 'current animation phase')
    connect(visual.find_result_pin(), phase.find_self_pin(), 'resident phase')
    before = add_function_call(graph, '/Script/Engine.KismetMathLibrary:LessEqual_DoubleDouble', -750, -1200, 'before gesture')
    after = add_function_call(graph, '/Script/Engine.KismetMathLibrary:GreaterEqual_DoubleDouble', -750, -1000, 'after gesture')
    for comparison, boundary in ((before, 1), (after, 4)):
        connect(phase.find_result_pin(), comparison.find_input_pin('A'), 'clip time')
        set_pin(comparison.find_input_pin('B'), boundary, 'common pose boundary')
    resting = add_function_call(graph, '/Script/Engine.KismetMathLibrary:BooleanOR', -450, -1100, 'matching authored poses')
    connect(before.find_result_pin(), resting.find_input_pin('A'), 'pre-gesture rest')
    connect(after.find_result_pin(), resting.find_input_pin('B'), 'post-gesture rest')
    transition = add_function_call(graph, '/Script/Engine.KismetMathLibrary:BooleanAND', -150, -700, 'safe clip transition')
    connect(changed.find_result_pin(), transition.find_input_pin('A'), 'new requested state')
    connect(resting.find_result_pin(), transition.find_input_pin('B'), 'common pose')
    branch = graph.add_branch_node()
    connect(guard.find_then_pin(), branch.find_execute_pin(), 'check animation transition')
    connect(transition.find_result_pin(), branch.find_condition_pin(), 'transition at common pose')
    cache_phase = add_set(graph, 'TransitionPhase', 0, -500)
    connect(phase.find_result_pin(), member_value_pin(cache_phase, 'TransitionPhase'), 'cache before replacing clip')
    connect(branch.find_then_pin(), cache_phase.find_execute_pin(), 'preserve clip phase')
    store = add_set(graph, 'TalkPlaying', 150, 0)
    connect(equal.find_result_pin(), member_value_pin(store, 'TalkPlaying'), 'remember state')
    connect(cache_phase.find_then_pin(), store.find_execute_pin(), 'change animation once')
    choose = graph.add_branch_node()
    connect(store.find_then_pin(), choose.find_execute_pin(), 'select clip')
    connect(equal.find_result_pin(), choose.find_condition_pin(), 'speaking clip')
    for execution, animation, y in ((choose.find_then_pin(), talk, 0), (choose.find_else_pin(), idle, 250)):
        play = add_function_call(graph, '/Script/Engine.SkeletalMeshComponent:PlayAnimation', 500, y, 'resident animation')
        connect(visual.find_result_pin(), play.find_self_pin(), 'animated resident')
        set_pin(play.find_input_pin('NewAnimToPlay'), animation.get_path_name(), 'authored clip')
        set_pin(play.find_input_pin('bLooping'), 'true', 'loop restrained movement')
        connect(execution, play.find_execute_pin(), 'play on transition')
        saved_phase = add_get(graph, 'TransitionPhase', 750, y - 100)
        resume = add_function_call(graph, '/Script/Engine.SkeletalMeshComponent:SetPosition', 950, y, 'continue shared pose phase')
        connect(visual.find_result_pin(), resume.find_self_pin(), 'animated resident')
        connect(saved_phase.find_result_pin(), resume.find_input_pin('InPos'), 'phase before clip replacement')
        set_pin(resume.find_input_pin('bFireNotifies'), 'false', 'no skipped notify replay')
        connect(play.find_then_pin(), resume.find_execute_pin(), 'resume without pose reset')
    # Gentle physical acknowledgement. Clamp turn to 12 degrees; do not navigate.
    location = add_function_call(graph, '/Script/Engine.Actor:K2_GetActorLocation', -1200, 500, 'resident location')
    player_location = add_function_call(graph, '/Script/Engine.Actor:K2_GetActorLocation', -1200, 700, 'Player location')
    connect(player.find_result_pin(), player_location.find_self_pin(), 'nearby Player position')
    look = add_function_call(graph, '/Script/Engine.KismetMathLibrary:FindLookAtRotation', -900, 500, 'acknowledge Player')
    connect(location.find_result_pin(), look.find_input_pin('Start'), 'resident position')
    connect(player_location.find_result_pin(), look.find_input_pin('Target'), 'Player position')
    split = add_function_call(graph, '/Script/Engine.KismetMathLibrary:BreakRotator', -650, 500, 'attention yaw')
    connect(look.find_result_pin(), split.find_input_pin('InRot'), 'attention direction')
    clamp = add_function_call(graph, '/Script/Engine.KismetMathLibrary:FClamp', -400, 500, 'subtle attention limit')
    connect(split.find_output_pin('Yaw'), clamp.find_input_pin('Value'), 'look yaw')
    set_pin(clamp.find_input_pin('Min'), -12, 'left limit')
    set_pin(clamp.find_input_pin('Max'), 12, 'right limit')
    distance = add_function_call(graph, '/Script/Engine.Actor:GetDistanceTo', -900, 900, 'acknowledgement distance')
    connect(player.find_result_pin(), distance.find_input_pin('OtherActor'), 'Player distance')
    near = add_function_call(graph, '/Script/Engine.KismetMathLibrary:Less_DoubleDouble', -650, 900, 'nearby only')
    connect(distance.find_result_pin(), near.find_input_pin('A'), 'distance')
    set_pin(near.find_input_pin('B'), 300, 'attention range')
    select = add_function_call(graph, '/Script/Engine.KismetMathLibrary:SelectFloat', -150, 500, 'rest when Player leaves')
    connect(clamp.find_result_pin(), select.find_input_pin('A'), 'nearby turn')
    set_pin(select.find_input_pin('B'), 0, 'rest yaw')
    connect(near.find_result_pin(), select.find_input_pin('bPickA'), 'Player nearby')
    rotation = add_function_call(graph, '/Script/Engine.KismetMathLibrary:MakeRotator', 100, 500, 'attention rotation')
    connect(select.find_result_pin(), rotation.find_input_pin('Yaw'), 'limited yaw')
    current = add_function_call(graph, '/Script/Engine.Actor:K2_GetActorRotation', 100, 800, 'current attention')
    interp = add_function_call(graph, '/Script/Engine.KismetMathLibrary:RInterpTo', 350, 500, 'smooth acknowledgement')
    connect(current.find_result_pin(), interp.find_input_pin('Current'), 'current turn')
    connect(rotation.find_result_pin(), interp.find_input_pin('Target'), 'target turn')
    connect(tick.find_output_pin('DeltaSeconds'), interp.find_input_pin('DeltaTime'), 'frame duration')
    set_pin(interp.find_input_pin('InterpSpeed'), 1.2, 'restrained turn speed')
    turn = add_function_call(graph, '/Script/Engine.Actor:K2_SetActorRotation', 600, 500, 'acknowledge without walking')
    connect(interp.find_result_pin(), turn.find_input_pin('NewRotation'), 'smoothed turn')
    connect(branch.find_else_pin(), turn.find_execute_pin(), 'idle presentation update')


def build():
    mesh = import_fbx('SK_NPC_A')
    nanite = mesh.get_editor_property('nanite_settings')
    nanite.set_editor_property('enabled', False)
    mesh.set_editor_property('nanite_settings', nanite)
    skeleton = mesh.get_editor_property('skeleton')
    idle, talk = import_fbx('A_Idle', skeleton), import_fbx('A_Talk', skeleton)
    materials = {
        'Skin': character_material('Skin', 'middleage_lightskinned_male_diffuse.png', 0.65),
        'ShirtDenim': character_material('ShirtDenim', 'male_casualsuit03_diffuse.png', 0.82, normal='male_casualsuit03_normal.png'),
        'Shoes': character_material('Shoes', 'shoes01_diffuse.png', 0.6),
        'Hair': character_material('Hair', 'short02_diffuse.png', 0.6, True),
        'Eyes': character_material('Eyes', 'brown_eye.png', 0.18, True),
        'Brows': character_material('Brows', 'eyebrow002.png', 0.85, True),
        'Lashes': character_material('Lashes', 'eyelashes01.png', 0.85, True),
    }
    slots = mesh.get_editor_property('materials')
    for index, slot in enumerate(slots):
        slot.material_interface = materials[str(slot.material_slot_name)]
        slots[index] = slot
    mesh.set_editor_property('materials', slots)
    parent = unreal.load_asset('/Game/Blueprints/BP_DialogueNPC')
    blueprint = unreal.BlueprintEditorLibrary.create_blueprint_asset_with_parent(BLUEPRINT, parent.generated_class())
    visual = add_component(blueprint, unreal.SkeletalMeshComponent, 'CharacterVisual')
    visual.set_skeletal_mesh_asset(mesh)
    visual.set_editor_property('relative_location', unreal.Vector(0, 0, -90))
    visual.set_editor_property('relative_rotation', unreal.Rotator(yaw=-90))
    visual.set_editor_property('relative_scale3d', unreal.Vector(1.08, 1.08, 1.08))
    visual.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    visual.set_editor_property('visibility_based_anim_tick_option', unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
    visual.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    data = visual.get_editor_property('animation_data')
    data.anim_to_play = idle
    data.saved_looping = True
    data.saved_playing = True
    visual.set_editor_property('animation_data', data)
    add_presentation_graph(blueprint, idle, talk)
    compile_and_save(blueprint)
    save_blueprint(blueprint)
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    require(level.load_level('/Game/Maps/L_Testbed'), 'testbed map')
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    previous = next(actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == 'NPC_A')
    npc = actors.spawn_actor_from_class(blueprint.generated_class(), previous.get_actor_location(), unreal.Rotator())
    npc.set_editor_property('DialogueLines', previous.get_editor_property('DialogueLines'))
    actors.destroy_actor(previous)
    npc.set_actor_label('NPC_A')
    require(level.save_current_level(), 'save refined resident')
    unreal.EditorAssetLibrary.save_directory(DEST, only_if_is_dirty=False, recursive=True)
    unreal.log('T06_NPC_A_GENERATION_PASSED')


if __name__ == '__main__':
    build()
