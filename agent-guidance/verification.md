# Verification

Agents run the complete verifier before committing executable or content changes:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -RequireVisualReview
```

Humans may run the deterministic local suite without an agent-mediated visual review:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

The verifier is green only when every required gate passes for the current working tree:

1. Validate every external asset against `ASSETS.md`, including source, license, local file coverage, and public-redistribution permission.
2. Validate the Unreal project, configured game map, and referenced content.
3. Compile every project Blueprint with zero errors and zero warnings.
4. Run the headless interaction functional tests and export their report.
5. Cook and package the Win64 build successfully.
6. Scan project, test, cook, and package logs with zero project-originated errors or warnings.
7. In agent mode, capture the four acceptance views and complete the multimodal visual gate below. In human-local mode, report this gate as not applicable.
8. Generate the local verification dashboard described by `verification-dashboard.md`.

Run focused gates while iterating, then run the complete command after all changes. A failed or skipped gate required by the active mode keeps verification red. A visual gate marked not applicable in human-local mode does not prevent the deterministic suite from passing.

## Warning exceptions

Treat a diagnostic as an exception only when it originates outside project-controlled content, cannot be removed with the pinned toolchain, and has no effect on the verified workflows. Record its exact stable match, origin, evidence, and consequence in the verifier's exception manifest. Unrecorded warnings fail the run; broad filters are invalid.

## Multimodal visual gate

In agent mode, the verifier captures the Room A overview, NPC A at dialogue distance, open-door transition, and Room B with NPC B. A multimodal agent must inspect the resulting images at full available detail against the prototype's visual rubric, then write a pass/fail review tied to the tested Git revision and every screenshot hash. The review covers visible rendering failures, composition, lighting, material quality, furnishing density, NPC presentation, UI obstruction, and whether the images plausibly meet the documented unmodded Skyrim Special Edition/Fallout 4 PC Ultra benchmark at normal gameplay distance.

This gate is agent-mediated: the local script proves capture freshness and review linkage, while the multimodal inspection supplies the visual judgement. A missing, stale, or unevidenced review fails agent-mode verification. Human-local validation skips visual capture and review without adding an external AI dependency.

## Performance

Record resolution and readily available frame timing with the acceptance capture. Performance is observational for this proof of concept and is not a hard gate. Do not add extended profiling unless observed performance prevents interaction or visual review.

## Completion evidence

Report the canonical command, its exit status, the dashboard path, the packaged-build path, the inspected screenshot, the multimodal review result, and every exception. State any untested behaviour explicitly.
