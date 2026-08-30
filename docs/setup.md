# T02 setup, editor, validation, and packaging

## Pinned environment

The T02 implementation targets:

| Tool | Version | Required C:-drive location |
| --- | --- | --- |
| Windows | Windows 11 Pro 25H2, build 26200.9168 on the implementation host | `C:\Windows` |
| Unreal Engine | 5.8.2, build `++UE5+Release-5.8-CL-56702186` | `C:\Program Files\Epic Games\UE_5.8` |
| Project clone | Git working tree | `C:\docs\git\fpsOne` |
| Git | 2.55.0.windows.2 | Host installation on C: |
| Git LFS | 3.7.1 | Host installation on C: |
| Windows PowerShell | 5.1.26100.9168 | `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe` |

The validator records the detected tool versions with every result. Assets committed through T02 were generated and verified with the build above.

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

Press Play to start in Room A facing the shared Door. The packaged and editor-play controls are identical: W/A/S/D move, the mouse looks, E uses the focused Interactable, and Escape exits.

## Safe Blueprint regeneration

Committed assets work directly from a fresh clone. To rebuild them after editing the generators, close all Unreal Editor and commandlet processes and run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\regenerate-assets.ps1
```

This creates an isolated project containing only the current project configuration, generators, and PIE test. It generates and compiles every Blueprint there, then runs the E-input Interaction test before touching the checkout's assets. The complete validated set is published with per-file atomic replacement and rollback if a later replacement fails. The workflow refuses to run or publish while any Unreal Editor process exists, even when its project cannot be identified; do not start an editor during regeneration. Originals, staged assets, logs, and the test report remain under `Saved\AssetRegeneration\<run-id>` for recovery; generation or test failures leave the original asset set untouched.

Direct execution of `bootstrap_project.py` now refuses an existing asset set. Do not delete committed assets to work around that guard. Regeneration intentionally replaces the generated blockout and Blueprints, so preserve any hand-edited asset work before running it.

## Canonical validation

Agent mode:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -RequireVisualReview
```

Human-local mode:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

The command validates the asset manifest, repository tests, project files, Blueprint compilation, the player-facing T02 Interaction scenario, Development Win64 packaging, a real packaged-window launch, project-originated diagnostics, and evidence freshness. T02 has no final Room, Door, or NPC acceptance views, so its four-view visual gate is explicitly not applicable until T08.

Generated evidence is under `C:\docs\git\fpsOne\Saved\Verification`:

- `verification-result.json` — machine-readable source of truth;
- `index.html` — local static dashboard;
- `logs\` — retained gate logs, the repository-test XML report, and a run-specific Unreal Automation HTML/JSON report; the dashboard links directly to each current report.

The Development package is archived to `C:\fpsOne-output\Development`. Override either location with `-EvidenceRoot` or `-PackageRoot` when necessary; keep both on C:.

## Manual acceptance

Prerequisite: a green canonical validation and `C:\fpsOne-output\Development\Windows\FPSOne.exe` (the exact path is also shown in the dashboard).

1. Launch `FPSOne.exe`; expect Room A, the centre dot, and the closed Door to appear without an editor or menu.
2. Hold W, S, A, and D separately, including while looking steeply up or down; expect forward, backward, left, and right walking while the player remains on the floor.
3. Move the mouse horizontally and vertically; expect conventional first-person view movement.
4. Try Space, Shift, Ctrl, and a connected controller; expect no jump, sprint, crouch, or controller action.
5. Stand within 250 cm and look directly at the Door; expect `E — Open` on a restrained lower-centre charcoal backing. Look away, step out of range, or place a wall between the view and Door; expect the prompt to clear.
6. Press E; expect the Door to ease 90° inward into Room B over about 0.75 seconds and permit passage. From Room B, refocus it, expect `E — Close`, press E, and expect the Door to reverse and block passage again once closed.
7. Press Escape; expect the application to exit immediately without opening a menu.

The T02 package has no NPC, dialogue, audio, furnishing, or final visual-quality acceptance content; those remain assigned to later tickets.
