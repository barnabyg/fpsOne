# Room A: preparation and acceptance

T04 dresses a 6 × 5 m living room with a 2.7 m ceiling. The warm wood, neutral woven upholstery, sage wall, bronze details, and restrained geometric art form one palette. A south-facing window supplies late-afternoon light; a floor lamp and wall sconce provide warm practical light. The exterior parapet is an inaccessible lighting backdrop, not another playable area. T05 finishes [Room B and the Door transition](room-b.md); both NPCs remain proxies until T06/T07.

The accepted PlayerStart is `(-550, -120, 90)` cm with yaw 23° and pitch −6°. NPC A sits to the left of the initial view and the closed Door is visible farther ahead; neither starts under Interaction Focus. The centre dot remains the only initial UI. Test-only occlusion and generic Interactable fixtures are created in an unsaved test setup and are absent from normal gameplay.

## Reproduce the assets

A Git LFS clone contains the ready-to-open map, imported assets, and editable sources. After cloning, run `git lfs pull` and `git lfs fsck`. Source and output hashes are recorded in `SourceArt/asset-manifest.json`; no Fab or other account entitlement is required for art.

To rebuild after editing the Unreal generator, close Unreal editors and commandlets, then run the documented `scripts/regenerate-assets.ps1`. It checks pinned source hashes before generation, imports the retained glTF/GLB and 2K textures in an isolated project, builds the Room, compiles Blueprints, and runs the player-facing scenario. It validates the staged provenance manifest before publishing assets and their manifest together with rollback and retained backups. `scripts/room_a_assets.py` owns Room A's material construction, positions, lights, collision, and composition. Generation does not run at game startup.

To edit the authored furniture, use portable [Blender 4.5.3 LTS](https://download.blender.org/release/Blender4.5/) on C:. Run:

```powershell
& 'C:\path\to\blender-4.5.3-windows-x64\blender.exe' --background --factory-startup --python .\scripts\create_room_a_furniture.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\regenerate-assets.ps1
```

The Blender script is the retained editable source. Its four GLB exports are the import inputs; no `.blend` duplicate is necessary. External glTF sources remain editable with all linked texture maps. If a pinned external source is missing, `scripts/restore-art-sources.ps1` can recover it from its recorded URL and verifies SHA-256 before installation. It never overwrites changed local sources. The normal clone and regeneration path do not need that download step.

## Current visual evidence

Run the canonical agent verifier:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -RequireVisualReview
```

The rendered Interaction scenario captures the real spawn view at 2560 × 1440, then runs the Door and both dialogue regressions. The verifier retains the screenshot and capture metadata in a run-specific directory beneath `Saved\Verification`. It records the exact revision, working-tree fingerprint, screenshot SHA-256, resolution, and observed frame duration. The first run exits 1 with **Room A visual review: missing** until the agent inspects the image. This is not a deterministic test failure.

Inspect the screenshot at full detail, including composition, lighting, material quality, furnishing density, rendering defects, and UI obstruction. Write `review.json` at the `roomA.reviewPath` named in `verification-result.json`:

```json
{
  "status": "passed",
  "reviewer": "Name of inspecting agent",
  "revision": "exact result.revision",
  "fingerprint": "exact result.fingerprint",
  "screenshotSha256": "exact result.roomA.sha256",
  "criteria": {
    "composition": { "status": "passed", "evidence": "Specific visible observations" },
    "lighting": { "status": "passed", "evidence": "Specific visible observations" },
    "materials": { "status": "passed", "evidence": "Specific visible observations" },
    "density": { "status": "passed", "evidence": "Specific visible observations" },
    "renderingDefects": { "status": "passed", "evidence": "Specific visible observations" },
    "uiObstruction": { "status": "passed", "evidence": "Specific visible observations" }
  }
}
```

Do not fill this template with a pass without inspecting the image. Failed criteria need correction and a fresh complete run. After a passing review:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -RequireVisualReview -CompleteVisualReview
```

From T05, Room B and the open-Door image also require separate current reviews using this schema and their own screenshot hashes. Completion accepts only the unchanged tested tree and exact reviewed screenshot, requires evidence for all six criteria, and refuses other failed deterministic gates. It updates the dashboard without recapturing a different image. T08's four-view benchmark including final NPC art remains separate. Human-local verification omits both agent switches and reports judgement as not applicable.

## Manual checks

After successful verification, launch the Development `Windows\FPSOne.exe` listed on the dashboard. At the initial spawn, expect a furnished living room, no E prompt, an off-centre NPC, and a clearly visible closed Door. Inspect the seating, rug, cabinet, window trim, and practical fixtures from ordinary walking distance; expect grounded furniture, fine surface detail, and no missing materials or conspicuous clipping.

Walk along the clear aisle to the Door, open it with E, cross into Room B, and close it from that side. Expect the decorative Door details to move with the leaf and the existing collision behavior to remain unchanged. Return and speak to NPC A, then NPC B; expect both exchanges, the hidden/restored dot, and restored walking to behave as before. Approach furniture and the window; expect solid collision rather than passage through them. Escape still exits immediately.
