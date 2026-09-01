# Setup, editor, validation, and packaging

## Pinned environment

The completed prototype targets:

| Tool | Version | Required C:-drive location |
| --- | --- | --- |
| Windows | Windows 11 Pro 25H2, build 26200.9168 on the implementation host | `C:\Windows` |
| Unreal Engine | 5.8.2, build `++UE5+Release-5.8-CL-56702186` | `C:\Program Files\Epic Games\UE_5.8` |
| Project clone | Git working tree | `C:\docs\git\fpsOne` |
| Git | 2.55.0.windows.2 | Host installation on C: |
| Git LFS | 3.7.1 | Host installation on C: |
| Windows PowerShell | 5.1.26100.9168 | `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe` |

The validator records the detected tool versions with every result. Unreal assets use the build above. T04's authored furniture uses Blender 4.5.3 LTS; Blender is only needed to edit/re-export those sources, not to open or package the committed project. Run `git lfs pull` after cloning to obtain the art binaries.

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

Press Play to start facing the furnished Room A, with NPC A off-centre and the shared Door visible but unfocused. The packaged and editor-play controls are identical: W/A/S/D move, the mouse looks, E uses the focused Interactable, and Escape exits.

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

The command validates per-file art provenance and hashes, a separate clean checkout with all 190 Git LFS files materialized, repository tests, project files, Blueprint compilation, the player-facing Interaction scenario, Development and Shipping Win64 packaging, a real Development packaged-window launch, project-originated diagnostics, evidence freshness, and all accepted 2560 × 1440 captures. Dialogue, replay, collision, suspended controls, restored controls, session reset, five slice reviews, and the final four-view benchmark remain required.

The first run is expected to exit 1 after producing current evidence because manual Shipping acceptance (and, in agent mode, visual judgement) cannot be claimed by an unattended command. Do not rebuild or edit the working tree between the following steps.

Generated evidence is under `C:\docs\git\fpsOne\Saved\Verification`:

- `verification-result.json` — machine-readable source of truth;
- `index.html` — local static dashboard;
- `logs\` — retained gate logs, the repository-test XML report, and a run-specific Unreal Automation HTML/JSON report; the dashboard links directly to each current report.

The Development and Shipping packages are archived to `C:\fpsOne-output\Development` and `C:\fpsOne-output\Shipping`. Override them with `-PackageRoot` or `-ShippingPackageRoot`. Clean-clone scratch space defaults to `C:\fpsOne-output\CleanClone`; each verified clone is removed after its evidence is recorded.

Run the guided walkthrough against the exact Shipping executable stored in `verification-result.json`:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\record-shipping-acceptance.ps1
```

The recorder launches at 2560 × 1440 and writes `Saved\Verification\shipping-manual-acceptance.json` only after every required check is explicitly confirmed with observed evidence and Escape has closed the application. It records the tested revision, complete working-tree fingerprint, executable path/hash, reviewer, resolution, and checklist.

After writing the current visual reviews, agent completion validates the unchanged evidence and also creates the delivery:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -RequireVisualReview -CompleteVisualReview
```

Human-local completion uses:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -CompleteDelivery
```

The final ZIP is `C:\fpsOne-output\Delivery\fpsOne-<12-character-revision>-win64-shipping.zip`. Its SHA-256, both executable locations, manual record, logs, reviews, durations, tool versions, revision/fingerprint, and exceptions appear in the final dashboard.

## Manual acceptance

Prerequisite: the first canonical run has passed every deterministic gate and produced the exact `C:\fpsOne-output\Shipping\Windows\FPSOne.exe` recorded in the dashboard. Use `record-shipping-acceptance.ps1`; the detailed expectations below define what must be observed before typing `PASS`.

1. Launch `FPSOne.exe`; expect Room A, the centre dot, and the closed Door to appear without an editor or menu.
2. Hold W, S, A, and D separately, including while looking steeply up or down; expect forward, backward, left, and right walking while the player remains on the floor.
3. Move the mouse horizontally and vertically; expect conventional first-person view movement.
4. Try Space, Shift, Ctrl, and a connected controller; expect no jump, sprint, crouch, or controller action.
5. Stand within 250 cm and look directly at the Door; expect `E — Open` on a restrained lower-centre charcoal backing. Look away, step out of range, or place a wall between the view and Door; expect the prompt to clear.
6. Press E; expect the Door to ease 90° inward into Room B over about 0.75 seconds and permit passage. From Room B, refocus it, expect `E — Close`, press E, and expect the Door to reverse and block passage again once closed.
7. Press Escape; expect the application to exit immediately without opening a menu.

For T03 dialogue acceptance:

1. In either Room, approach the resident and look at it from within 250 cm. Expect `E — Talk` in the same prompt presentation as the Door. Walk into the NPC; expect its capsule to block passage.
2. Press E once. Expect a restrained charcoal panel near the bottom with a speaker-labelled line. The centre dot and Talk prompt disappear.
3. Hold each movement key during dialogue; expect no walking. Move the mouse in both axes; expect limited look (35 degrees horizontally and 20 degrees vertically around the starting view).
4. Press E separately for each line. Expect three lines, then dismissal on the next press. Expect the centre dot, contextual prompts, walking, and free look to return. Repeat with each NPC several times; each exchange starts from its own first line.
5. Exit during an exchange with the Door open, then relaunch. Expect a closed Door, no dialogue panel, normal controls, and both exchanges available from the beginning.

The NPC's instance-editable `DialogueLines` array contains speaker-labelled text entries (for example, `Resident A: ...` and `Player: ...`). Each NPC owns its own copy; the shared Interaction component handles the active exchange. Empty arrays do not start an exchange. No dialogue state is persisted.

To capture the dialogue and restored HUD for visual inspection, run the functional scenario with rendering enabled:

```powershell
& 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' "$PWD\FPSOne.uproject" '-ExecCmds=Automation RunTests Editor.Python.FPSOne.test_interaction' '-TestExit=Automation Test Queue Empty' -T03Capture -ResX=2560 -ResY=1440 -unattended -nop4 -nosplash
```

Captures are retained under `Saved\DialogueReview` at the PIE viewport's actual resolution (recorded by the pixel check; command-line window size does not force the embedded viewport size). The canonical verifier runs this rendered scenario after its headless scenario and checks the actual pixels for dot hiding/restoration and panel dismissal. Both captures and the pixel report appear on the dashboard. This deterministic T03 UI check is separate from the T08 final-art benchmark.

The Shipping package contains both furnished Rooms and both refined animated residents. Audio remains outside the prototype's scope.
