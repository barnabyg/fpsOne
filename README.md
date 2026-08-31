# fpsOne

fpsOne is a narrowly scoped first-person Unreal Engine 5.8 testbed with two furnished apartment Rooms, an animated Door, and repeatable dialogue. T06 replaces NPC A with a CC0 humanoid with idle motion, blinks, nearby acknowledgement, and a conversational gesture. NPC B remains a proxy until T07. All art is publicly redistributable.

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

## Open the editable project

Open `FPSOne.uproject` from Epic Games Launcher or run:

```powershell
& 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe' "$PWD\FPSOne.uproject"
```

The project starts on `/Game/Maps/L_Testbed` and uses `/Game/Blueprints/BP_TestbedGameMode` with `/Game/Blueprints/BP_Player` as its default pawn. Look directly at the Door from within 250 cm to see `E — Open` or `E — Close`; the centre dot remains visible during free movement and no outline or glow is used. `/Game/Blueprints/BP_TestbedPlayerController` disables motion input at the controlled-player boundary; no controller mappings are present.

## Validate and package

Agents run the complete current-slice validation:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -RequireVisualReview
```

Humans run the same repository tests, deterministic compile, player-facing PIE Interaction scenario, Development package and launch smoke test, and diagnostics without agent visual judgement:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

Evidence and the local dashboard are written to `Saved\Verification`; the Development package defaults to `C:\fpsOne-output\Development`. Both locations are outside version control.

T04 adds a 2560 × 1440 Room A acceptance image and an agent review linked to its hash and the tested working tree. The initial agent run remains red until that review is completed with `verify.ps1 -RequireVisualReview -CompleteVisualReview`. See [Room A assets, visual review, and manual checks](docs/room-a.md). A normal clone needs Git LFS assets (`git lfs pull`); asset downloads and Blender are unnecessary to open or play it.

The current verifier also requires Room B, open-Door, and conversational-distance NPC A captures and reviews. See [NPC A source, pinned authoring tools, and manual checks](docs/npc-a.md) and [Room B](docs/room-b.md). Blender 4.5.3, MPFB 2.0.8, and MakeHuman core assets are needed only to recreate or change character source; their SHA-256 pins and C:-only setup are included without tool binaries.
