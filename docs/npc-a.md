# NPC A: source, animation, and acceptance

T06 replaces Resident A with a CC0 adult humanoid: a textured striped shirt,
denim, leather shoes, layered short hair, brown eyes, and a calibrated rough
skin material. The approximately 180 cm resident retains the existing blocking
capsule and NPC-owned dialogue. T07 adds [the distinct NPC B resident](npc-b.md)
using the same source and presentation workflow.

`BP_NPC_A` inherits `BP_DialogueNPC`; its construction script hides only the
inherited proxy art. `CharacterVisual` uses the imported MPFB skeleton, without
Nanite or mesh collision. The capsule still blocks the Player. The shared
Interaction component remembers its `DialogueActor` during an exchange and
releases it on dismissal; it contains no NPC-type branches. The resident plays
an eight-second breathing idle, two short blinks per cycle, and a restrained
right-hand conversational gesture while it is the active speaker. Clip changes
wait for a common rest pose and retain breathing/blink phase: dismissal lets
the current arm movement settle without delaying control restoration; replay
can continue that movement. A new gesture can wait until the next eight-second
cycle. It
smoothly turns at most 12 degrees toward a Player within 300 cm and returns to
rest outside that range. This is a small whole-body acknowledgement, not gaze
tracking or navigation. No voice, lip-sync, cinematic face system, or movement
controller is added.

## Pinned tools on C:

Normal Git LFS clones need no Blender, MPFB, downloads, or account entitlement
to open, play, validate, or regenerate Unreal content. The authoring tools are
optional and stay in ignored storage. `Build/character-toolchain.json` pins
Blender 4.5.3 portable, MPFB 2.0.8, and the MakeHuman system asset pack by exact
archive SHA-256. MPFB code is GPL; its graphical inputs and outputs are CC0.
The tools themselves are not committed.

From the repository root, with public download access:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-character-tools.ps1
$tools = "$PWD\.scratch\character-tools"
$env:BLENDER_USER_RESOURCES = "$tools\blender-user"
& "$tools\blender\blender-4.5.3-windows-x64\blender.exe" --background --factory-startup --python-exit-code 1 --python .\scripts\create_npc.py -- --tools $tools --resident A
```

The setup script accepts `-ToolRoot` for another directory on C:, verifies each
archive before extraction, and rejects altered downloads. It uses Blender's
local extension repository without changing a person's normal Blender setup.
Do not put the tool directory in a tracked content folder.

## Editable source and export

`SourceArt/Characters/NPC_A/NPC_A.blend` retains the rig, weighted meshes,
materials, and the `A_Idle` and `A_Talk` actions. Texture paths are relative to
the blend file. The original macro prescription, selected parts, and animation
curves are also editable in `scripts/character_recipes.py` and
`scripts/create_npc.py`. `recipe.json` records
the prescription and each retained texture's archive path, upstream hash,
and final hash. The clothing normal map is reduced to 2K; smaller eye, shoe,
and eyelash maps are retained at native size rather than upscaled.

The script bakes the macro shape, removes helpers and clothing-covered body
faces, subdivides exposed skin once, and exports `SK_NPC_A.fbx`, `A_Idle.fbx`,
and `A_Talk.fbx`. The 30 fps clips span frames 1–241. Export uses selection
only, `-Y` forward, `Z` up, face smoothing, no leaf bones, no NLA strips, one
action per animation file, and no animation simplification. The explicit
`ResidentARig` root is intentional: Unreal's legacy FBX importer strips a root
named `Armature`, which otherwise collapses the animation's centimetre scale.

To reproduce imported content from the retained sources, close Unreal editors:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\regenerate-assets.ps1
```

The isolated generation project creates gameplay, both Rooms, then both residents using
`scripts/npc_assets.py`. It imports the mesh and clips with the pinned legacy
skeletal FBX importer, supplies the same skeleton to both clips, reconstructs
materials, and preserves the NPC's dialogue lines and position. It then runs
the Player Interaction scenario and publishes the assets and matching manifest
together, retaining rollback copies. Unreal asset GUIDs and blend metadata can
vary; reproducibility means equivalent geometry, materials, animation, and
behavior, not identical generated binary bytes.

After intentional Blender-source edits, inspect the exports and update only
their corresponding `files` SHA-256 entries in the character entry of
`SourceArt/asset-manifest.json` before regeneration. Never refresh upstream
texture hashes to accept unexplained changes. The generated-file updater
deliberately refuses changed pinned sources. Restore committed art with Git
LFS; `restore-art-sources.ps1` remains specifically for Poly Haven downloads.

## Provenance

`ASSETS.md` and the per-file manifest cover every retained character source,
texture, clip, material, mesh, and skeleton. The character folder retains the
upstream MPFB license statement, its full CC0 asset license, and an original
core-material copyright/CC0 notice. All animation is original fpsOne keyframe
work dedicated to CC0; no third-party motion capture or restricted content is
used. The blend and FBX files contain graphical output, not MPFB tool code.

## Current visual evidence

Run the complete agent verifier, inspect all five current screenshots, write
their linked reviews, and complete that same run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -RequireVisualReview
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -RequireVisualReview -CompleteVisualReview
```

The NPC A view is captured during the real first dialogue line, 150 cm in
front of the resident at Player location `(-110,-180,90)` (settled capsule
height can vary slightly), pitch 0°, yaw 180°, at 2560 × 1440. Its result key
is `npcA`; the dashboard links the image, metadata, and review. Use Room A's
review schema plus `npcPresentation` and `referenceBaseline` criteria. Each
requires a passed status and specific visible evidence. Examine face/eye/hair
integrity, clothing, scale, silhouette, and plausible unmodded Skyrim Special
Edition/Fallout 4 PC Ultra quality at this distance. Do not infer visual quality
from compilation or a successful import. T08's final complete-prototype
benchmark remains separate; NPC B has its own current character review from T07.

The deterministic Player scenario checks the imported resident's running head
height in both idle and dialogue, in addition to collision, both exchanges,
replay, scanning suspension, bounded look, restored controls, and new-session
reset. The dot/panel pixel regression looks at a fixed floor patch beside the
animated resident so moving skin and clothing cannot disguise a UI regression.
Human-local verification captures the same evidence without agent judgement.

## Manual checks

Prerequisite: complete verification, then launch the Development executable
linked by `Saved/Verification/index.html`.

1. Approach NPC A near the living-room window. Expect a full-size clothed
   resident, no proxy primitives, grounded feet, readable eyes and hair, and
   `E — Talk` when directly focused within 250 cm. Try walking through the NPC
   from the front and side; expect blocking collision.
2. Watch for at least eight seconds. Expect slight breathing and natural short
   blinks; move a little to either side and beyond 300 cm. Expect a slow small
   acknowledgement followed by a return to rest, without walking or tracking
   the Player through a full turn.
3. Press E and leave a line visible for eight seconds. Expect a restrained
   right-hand gesture, no speech audio or mouth animation, hidden dot, paused
   walking, and limited mouse look. Advance three times to dismiss, then
   replay, including dismissal halfway through a raised-arm gesture. Expect the
   arm to settle without a snap and scanning, walking, and free look to return
   immediately. Replay during that return should remain smooth.
4. Open the Door and speak with NPC B. Expect its unchanged dialogue to work;
   NPC A should continue idling rather than gesture for NPC B's exchange.
5. Exit with Escape and relaunch. Expect the Door closed, both dialogues reset,
   and NPC A in its idle state.

The fixed screenshot does not establish animation timing or every viewing
angle. The temporal and close-angle manual checks remain useful alongside the
automated Interaction scenario.
