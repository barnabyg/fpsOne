# fpsOne

fpsOne is a narrowly scoped first-person Unreal Engine 5.8 testbed. T01 establishes a blank Blueprint-only project, a minimal playable space, conventional keyboard-and-mouse movement, immediate Escape exit, Development packaging, and local verification evidence.

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
| Escape | Exit immediately |

Sprinting, jumping, crouching, controller input, weapons, and menu behavior are intentionally absent.

## Open the editable project

Open `FPSOne.uproject` from Epic Games Launcher or run:

```powershell
& 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe' "$PWD\FPSOne.uproject"
```

The project starts on `/Game/Maps/L_Testbed` and uses `/Game/Blueprints/BP_TestbedGameMode` with `/Game/Blueprints/BP_Player` as its default pawn. `/Game/Blueprints/BP_TestbedPlayerController` disables motion input at the controlled-player boundary; no controller mappings are present.

## Validate and package

Agents run the complete current-slice validation:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -RequireVisualReview
```

Humans run the same repository tests, deterministic compile, Development package and launch smoke test, and diagnostics without agent visual judgement:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

Evidence and the local dashboard are written to `Saved\Verification`; the Development package defaults to `C:\fpsOne-output\Development`. Both locations are outside version control.
