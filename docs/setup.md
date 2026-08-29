# T01 setup, editor, validation, and packaging

## Pinned environment

The T01 implementation targets:

| Tool | Version | Required C:-drive location |
| --- | --- | --- |
| Windows | Windows 11 Pro 25H2, build 26200.9168 on the implementation host | `C:\Windows` |
| Unreal Engine | 5.8.2, build `++UE5+Release-5.8-CL-56702186` | `C:\Program Files\Epic Games\UE_5.8` |
| Project clone | Git working tree | `C:\docs\git\fpsOne` |
| Git | 2.55.0.windows.2 | Host installation on C: |
| Git LFS | 3.7.1 | Host installation on C: |
| Windows PowerShell | 5.1.26100.9168 | `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe` |

The validator records the detected tool versions with every result. Assets committed by T01 were generated and verified with the build above.

## Epic Games Launcher handoff

From Git Bash in the repository, run:

```bash
./scripts/setup-unreal.sh
```

The three stages are:

1. Download and install Epic Games Launcher on C:.
2. Sign in inside the Launcher, open **Unreal Engine → Library**, add version **5.8**, review and accept Epic's current terms, and install to `C:\Program Files\Epic Games\UE_5.8`. Keep the core engine and Windows target platform; templates, Starter Content, and marketplace content are not required.
3. Verify `UnrealEditor-Cmd.exe` and `RunUAT.bat`, then launch the editor once so first-run prerequisites complete.

The wizard writes `FPS_ONE_ENGINE_ROOT` to the ignored `.env` file. Credentials and licence state remain exclusively in Epic's software. These steps follow Epic's current [Install Unreal Engine](https://dev.epicgames.com/documentation/unreal-engine/install-unreal-engine) guidance.

## Editor startup

Open `FPSOne.uproject` or run:

```powershell
& 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe' 'C:\docs\git\fpsOne\FPSOne.uproject'
```

Press Play to start in the minimal test space. The packaged and editor-play controls are identical.

## Canonical validation

Agent mode:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -RequireVisualReview
```

Human-local mode:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

The command validates the asset manifest, repository tests, project files, Blueprint compilation, Development Win64 packaging, a real packaged-window launch, project-originated diagnostics, and evidence freshness. T01's input-surface tests are active; world Interaction functional tests activate with T02. T01 has no final Room, Door, or NPC acceptance views, so its four-view visual gate is explicitly not applicable until T08.

Generated evidence is under `C:\docs\git\fpsOne\Saved\Verification`:

- `verification-result.json` — machine-readable source of truth;
- `index.html` — local static dashboard;
- `logs\` — retained gate logs.

The Development package is archived to `C:\fpsOne-output\Development`. Override either location with `-EvidenceRoot` or `-PackageRoot` when necessary; keep both on C:.

## Manual acceptance

Prerequisite: a green canonical validation and `C:\fpsOne-output\Development\Windows\FPSOne.exe` (the exact path is also shown in the dashboard).

1. Launch `FPSOne.exe`; expect the minimal test space to appear without an editor or menu.
2. Hold W, S, A, and D separately, including while looking steeply up or down; expect forward, backward, left, and right walking while the player remains on the floor.
3. Move the mouse horizontally and vertically; expect conventional first-person view movement.
4. Try Space, Shift, Ctrl, and a connected controller; expect no jump, sprint, crouch, or controller action.
5. Press Escape; expect the application to exit immediately without opening a menu.

The T01 package has no Door, NPC, Interaction Prompt, dialogue, audio, or final visual-quality acceptance content; those remain assigned to later tickets.
