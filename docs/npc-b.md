# NPC B: source, animation, and acceptance

T07 replaces Room B's proxy with a second CC0 adult resident. A shorter, fuller
body and different face, brown ponytail, sage striped blouse, charcoal
skirt, and black shoes distinguish NPC B from NPC A's short hair, burgundy shirt,
denim, and taller silhouette. Both use rough skin and cloth materials calibrated
for the apartment lighting, masked hair and eye textures, and non-Nanite skeletal
meshes. The inherited blocking capsule and neutral dialogue are unchanged.

## Reproduce and edit

The pinned Blender 4.5.3, MPFB 2.0.8, and MakeHuman core archive are shared with
[NPC A](npc-a.md). The tools are optional for opening, playing, packaging, or
regenerating Unreal assets from a Git LFS clone. To recreate NPC B's source:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-character-tools.ps1
$tools = "$PWD\.scratch\character-tools"
$env:BLENDER_USER_RESOURCES = "$tools\blender-user"
& "$tools\blender\blender-4.5.3-windows-x64\blender.exe" --background --factory-startup --python-exit-code 1 --python .\scripts\create_npc.py -- --tools $tools --resident B
```

`scripts/character_recipes.py` holds both residents' macro prescriptions, selected
parts, material maps, scale, rest orientation, rest posture, irregular idle
timing, glances, hand adjustments, dialogue beats, and blink timing.
`scripts/create_npc.py` implements their common source workflow. NPC B uses the
MakeHuman `female_elegantsuit01`, `shoes03`, `ponytail01`, `eyebrow001`, `high-poly`
eyes, brown-eye material, `eyelashes01`, and middle-aged Asian female skin.

`SourceArt/Characters/NPC_B/NPC_B.blend` retains editable weighted meshes,
materials, the `ResidentBRig` skeleton, and `B_Idle` / `B_Talk` actions. Relative
texture paths work outside the author's checkout. `recipe.json` records macro
values, retained texture archive paths, upstream SHA-256 and final SHA-256.
Textures are at most 2K. The export emits `SK_NPC_B.fbx` plus both 30 fps,
24-second clips, with the same axis, scale, bone, and animation settings as
NPC A. Reproduction promises equivalent geometry and behavior, not identical
Blender metadata or Unreal asset GUIDs.

After intentional source edits, inspect the exported result and update only
the corresponding source `files` hashes in the `makehuman_npc_b` manifest entry.
Do not change upstream hashes to accept unexplained changes. With editors closed:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\regenerate-assets.ps1
```

Regeneration builds both Rooms and imports each resident through the same
`scripts/npc_assets.py` importer (the second invocation selects `-NPCB`). It
creates `BP_NPC_A` and `BP_NPC_B` from `BP_DialogueNPC`, hides only the inherited
proxy art, retains the dialogue arrays and Room positions, validates the Player
scenario, then publishes assets and the manifest transactionally. NPC B faces
the Room B approach at yaw 180 degrees. Attention is clamped to 12 degrees
relative to each resident's own rest direction and returns to rest beyond 300 cm.

Both residents keep planted feet and share a relaxed rest-pose vocabulary while
using different breathing, weight-shift, glance, blink, and hand-adjustment
timing. NPC B's mannerism favours two restrained left-hand conversational beats,
distinct from NPC A's right-hand movements. Idle/talk transitions preserve the
complete 24-second phase and wait for a common rest interval, so dismissal
restores controls immediately while a raised arm settles. The shared Interaction owns the active speaker;
speaking to one resident does not activate the other's talk animation. There is
no navigation, voice, lip-sync, or added dialogue system.

## Provenance

The character folder retains the upstream license statement, CC0 text, and
original core-material notice. All selected inputs are from the pinned CC0
MakeHuman core pack; all keyframed animation is original fpsOne work dedicated
to CC0. `ASSETS.md` and `SourceArt/asset-manifest.json` cover every retained
source, texture, clip, imported mesh, material, and skeleton. Tool code and
download archives remain outside Git.

## Current visual evidence

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -RequireVisualReview
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -RequireVisualReview -CompleteVisualReview
```

Between commands, inspect all five current views and write their linked reviews.
NPC B's `npcB` result is a 2560 x 1440 capture during its real first dialogue
line, from Player position `(160,25,90)` (settled capsule height can vary), pitch
0 and yaw 0, 150 cm from NPC B at `(310,25,90)`. The dashboard links the image,
capture metadata, and review. Use [Room A's review schema](room-a.md) with the
additional `npcPresentation` and `referenceBaseline` criteria required for both
NPC views. Each needs specific visible evidence, including comparison with NPC A
and plausible unmodded Skyrim Special Edition / Fallout 4 PC Ultra quality at
normal conversational distance. Missing, stale, substituted, or incomplete
reviews keep the agent run red. T08's final complete-prototype assessment remains
separate; human-local mode captures the evidence without agent judgement.

The Player scenario covers both imported residents' animated standing height,
blocking collision, original exchanges, replay, shared UI and fresh-session
reset. NPC B additionally exercises suspended walking/scanning, bounded look,
restored movement/free look, visible left-hand movement and a smooth dismissal.

## Manual checks

Prerequisite: green verification, then launch the Development executable linked
by `Saved/Verification/index.html` at 2560 x 1440.

1. Open the Door and approach NPC B beside the office window. Compare its face,
   body, ponytail, sage blouse and skirt with NPC A. Expect clearly distinct,
   full-size residents, grounded feet and no proxy shapes or broken materials.
2. Walk into NPC B from the front and sides. Expect blocking collision and a
   usable approach around the resident, desk, guest bed, and Door.
3. Watch for at least 24 seconds from the front and an oblique angle. Expect
   planted feet, relaxed arms and hands, subtle breathing, weight transfer,
   brief blinks, small glances, and occasional hand/finger adjustment without a
   repeated pendulum beat. Check that the feet neither float nor slide in world
   space and that arms, hands, and clothing do not penetrate the body; elbows,
   neutral wrists, and fingers must remain anatomically plausible. Compare NPC A
   and expect different timing and mannerisms. Move to either side and beyond
   300 cm; expect a small smooth acknowledgement and return to its Room B facing
   direction without a foot slide or pose snap.
4. Focus within 250 cm and press E. Expect `Resident B: I have just finished
   tidying the desk.` Hold/replay long enough to see both distinct left-hand
   gesture beats. Expect hidden dot/prompt, suspended walking and bounded mouse
   look while NPC A keeps idling.
5. Advance the three lines, dismiss during each raised-hand beat, and replay
   immediately. Expect smooth settling or continuation, immediate restored
   movement/scanning/free look, world-space foot planting, plausible joints
   without mesh penetration, unchanged dialogue, and independent residents.
6. Exit during dialogue with the Door open and relaunch. Expect the Door closed,
   no dialogue panel, normal input, and both residents available from line one.

A fixed acceptance image cannot establish every angle or blink/gesture timing;
the temporal manual checks complement the automated scenario and visual review.
