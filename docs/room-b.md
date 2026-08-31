# Room B: preparation and acceptance

T05 finishes the home office/guest room and the open-Door transition. Room B has a clear 400 × 400 cm footprint (`x=20..420`, `y=-200..200`) and a 270 cm ceiling. The shared partition ends at x=20; its thickness is outside that footprint. There is no corridor. The window opens visually onto an inaccessible courtyard backdrop and has a blocking boundary.

The oak workstation, upholstered chair, linen guest daybed, bookcase, woven rug, reading lamp, plant, books, pinboard, and original geometric prints share Room A's oak, sage, linen, charcoal, and bronze palette. An east window provides soft daylight with warm task and reading lights. Both sides of the Door have matching casing and a handle attached to the existing moving leaf. Furniture stays clear of the Door swing and the approach to NPC B. Both NPCs remain the T03 proxies pending T06/T07; T05 does not claim final character acceptance.

## Editable sources and generation

T06 subsequently replaces NPC A using the [pinned character workflow](npc-a.md); NPC B remains a proxy until T07. The current verifier additionally requires NPC A's conversational-distance review.

The normal Git LFS clone contains the ready-to-open map and imported assets. No new external assets or texture downloads are required: T05 reuses the seven pinned Poly Haven CC0 sources documented in [ASSETS.md](../ASSETS.md). All texture maps remain 2K and the four new GLB furniture sources add less than 3 MiB. The per-file manifest covers the exported and imported assets.

`scripts/create_room_b_furniture.py` is the editable Blender 4.5.3 source; it imports the existing modelling helpers without regenerating Room A. To edit the meshes:

```powershell
& 'C:\path\to\blender-4.5.3-windows-x64\blender.exe' --background --factory-startup --python .\scripts\create_room_b_furniture.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\regenerate-assets.ps1
```

`scripts/room_b_assets.py` owns placement, trim, lighting, and material assignment. The existing isolated regeneration workflow builds Room A, then Room B, tests the finished map through Player input, and publishes assets and their validated manifest together. No art generation runs at game startup. Close Unreal editors before regeneration.

## Repeatable acceptance

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -RequireVisualReview
```

The rendered Interaction scenario opens the real Door using E, then captures the transition from Player position `(-170,-55,90)` with pitch −6°, yaw 15°, and Room B from `(65,15,90)` with pitch −12°, yaw −8°. These are gameplay cameras with the normal HUD, not editor renders. The scenario also captures Room A's unchanged spawn view and the dialogue UI. All three environment views are 2560 × 1440; capture metadata includes the camera and observed frame duration (informational, not an FPS gate).

Agent verification stays red until all three images receive current visual reviews. Inspect the images named by `roomA`, `roomB`, and `doorTransition` in `Saved/Verification/verification-result.json`. Write a separate review to each view's `reviewPath`, following [Room A's existing JSON schema](room-a.md#current-visual-evidence), with that view's `sha256`, the run's revision and fingerprint, and specific visible evidence for composition, lighting, materials, density, rendering defects, and UI obstruction. Review the open-Door composition for continuity and absence of a corridor as part of composition. Do not mark a criterion passed without inspecting it.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -RequireVisualReview -CompleteVisualReview
```

Completion rejects any missing review, substituted image, stale tree, absent criterion evidence, or failed deterministic gate. The dashboard links all three screenshots, metadata, reviews, tests, logs, and the package. Human-local verification omits both agent switches; it captures all three views and explicitly marks agent judgement not applicable. T08's final four-view benchmark remains separate.

## Manual checks

Prerequisite: run verification successfully, then launch the Development `Windows\FPSOne.exe` shown on the dashboard.

1. Walk from the furnished living room to the Door and press E. Expect a smooth inward swing, matching trim and continuous flooring between the Rooms, with no corridor or visible void at the threshold.
2. Enter Room B, walk down the centre aisle, and inspect the workstation, guest bed, shelves, textiles, window, and practical lights. Expect grounded furnishings, readable surface detail, no missing materials, and no obstructing clutter.
3. Approach NPC B from the centre aisle. Expect `E — Talk`; advance all three lines with separate E presses, dismiss, and repeat. Expect walking and the centre dot to return after dismissal.
4. Approach the bed, desk, bookcase, and window. Expect solid collision and no route outside the apartment. Walk back to the open Door, look at its leaf, and press E to close it from Room B. Reopen and return to Room A; expect passage and NPC A's dialogue to work as before.
5. Exit with Escape and relaunch. Expect the closed Door, normal controls, and both exchanges reset.

Automated Player-capsule sweeps cover the Room B aisle, bed collision, window boundary, Door traversal and closing, and both NPC exchanges. The window check uses the clear south bay at standing height, first confirms an unobstructed approach, then requires the Player to stop at the exterior boundary. It checks the complete window assembly, not a particular invisible component. An isolated negative run with the whole window assembly's collision disabled must fail that assertion after the Player crosses x=420; unrelated failures do not establish sensitivity. Subjective close-range art quality beyond the fixed captures still benefits from the manual walk-through above.
