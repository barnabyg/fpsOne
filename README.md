# fpsOne

fpsOne is a narrowly scoped first-person Unreal Engine 5.8 testbed with two furnished apartment Rooms, an animated Door, and repeatable dialogue. T06 and T07 supply two distinct CC0 humanoid residents with idle motion, blinks, nearby acknowledgement, and conversational gestures. All art is publicly redistributable.

## Prerequisites

- Windows 11 on C:
- Epic Games Launcher and Unreal Engine 5.8.2
- Git 2.55.0.windows.2 and Git LFS 3.7.1
- Windows PowerShell 5.1 (the canonical verifier); PowerShell 7 is optional

Epic sign-in and licence acceptance are the only credential-bound setup steps. Run the guided setup from Git Bash:

```bash
./scripts/setup-unreal.sh
```

The wizard stores only the non-secret Unreal installation path in the ignored `.env` file. It never requests or stores Epic credentials. See [docs/setup.md](docs/setup.md) for exact locations and troubleshooting.

After cloning the repository, materialize the Unreal assets managed by Git LFS:

```powershell
git lfs pull
```

## Controls

| Input | Action |
| --- | --- |
| W / S | Move forward / backward |
| A / D | Move left / right |
| Mouse | Point the view |
| E | Use the focused Interactable; advance or dismiss dialogue |
| Escape | Exit immediately |

Sprinting, jumping, crouching, controller input, weapons, and menu behavior are intentionally absent.

Look at either NPC within 250 cm for `E — Talk`. E opens a shared speaker-labelled bottom panel, advances its three lines, then dismisses it. During dialogue, walking and Interaction scanning pause, the dot and prompt hide, and mouse look is limited around the starting view. Controls return on dismissal; either exchange can be replayed.

## Run the application

### From the Unreal Editor

Open `FPSOne.uproject` from Epic Games Launcher or run:

```powershell
& 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe' "$PWD\FPSOne.uproject"
```

When the project finishes loading, select **Play** in the editor toolbar to start the application in the editor. It opens on `/Game/Maps/L_Testbed`. Use the controls above; press Escape to exit the running application.

### From a packaged build

The canonical verifier creates Development and Shipping Windows builds. To create them, run this command from the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

The first verification pass is expected to report incomplete manual acceptance after it creates the packages. Launch the generated Development application using the exact run-specific path recorded by the verifier:

```powershell
$verification = Get-Content .\Saved\Verification\verification-result.json -Raw | ConvertFrom-Json
$developmentExecutable = [string] $verification.packages.development
& $developmentExecutable
```

Packaged builds are written below `Saved\Packages\Development` and `Saved\Packages\Shipping`; they are generated locally and ignored by Git. Use the Development build for routine play. The Shipping build is reserved for the guided acceptance and delivery workflow described below and in [docs/setup.md](docs/setup.md).

The project uses `/Game/Blueprints/BP_TestbedGameMode` with `/Game/Blueprints/BP_Player` as its default pawn. Look directly at the Door from within 250 cm to see `E — Open` or `E — Close`; the centre dot remains visible during free movement and no outline or glow is used. `/Game/Blueprints/BP_TestbedPlayerController` disables motion input at the controlled-player boundary; no controller mappings are present.

## Validate and package

Agents begin the complete validation and capture current deterministic and visual evidence:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -RequireVisualReview
```

Humans run the same asset, clean-clone, repository, Blueprint, player-facing Interaction, Development/Shipping package, Development launch, and diagnostic gates without agent visual judgement:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

That first run intentionally remains red until the exact Shipping executable completes the guided 2560 × 1440 walkthrough:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\record-shipping-acceptance.ps1
```

After the walkthrough, agents write the current visual reviews described in [final visual acceptance](docs/visual-acceptance.md) and complete both visual and delivery evidence:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -RequireVisualReview -CompleteVisualReview
```

Humans complete the same Shipping delivery without the agent-only visual judgement:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -CompleteDelivery
```

Evidence and the local dashboard are written to `Saved\Verification`. Development and Shipping packages default to `Saved\Packages\Development` and `Saved\Packages\Shipping`; the versioned ZIP and SHA-256 evidence default to `Saved\Delivery`. Temporary clean-clone verification uses `Saved\CleanClone`. The repository's `Saved/` ignore rule keeps all of these generated outputs out of version control.

T04 adds a 2560 × 1440 Room A acceptance image and an agent review linked to its hash and the tested working tree. The initial agent run remains red until that review is completed with `verify.ps1 -RequireVisualReview -CompleteVisualReview`. See [Room A assets, visual review, and manual checks](docs/room-a.md). A normal clone needs Git LFS assets (`git lfs pull`); asset downloads and Blender are unnecessary to open or play it.

The verifier also requires Room B, open-Door, and conversational-distance captures and reviews for both NPCs, plus one complete-prototype assessment across the four accepted gameplay views. The final gates stay red for missing, stale, substituted, or failed visual/manual evidence. See [NPC A and pinned authoring tools](docs/npc-a.md), [NPC B source and manual checks](docs/npc-b.md), and [Room B](docs/room-b.md). Blender 4.5.3, MPFB 2.0.8, and MakeHuman core assets are needed only to recreate or change character source; their SHA-256 pins and C:-only setup are included without tool binaries.
