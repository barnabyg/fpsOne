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
4. Run the headless interaction functional tests and export their report. From T03, also run the rendered Dialogue presentation scenario and pixel checks for the hidden/restored centre dot and appearing/dismissing panel; retain both UI screenshots on the dashboard. This deterministic UI regression gate is separate from T08's final-art multimodal acceptance.
5. Prove a separate clone of the canonical public remote can materialize all current Git LFS content and validate every editable source and license record.
6. Cook and package Development and Shipping Win64 builds into fresh run-specific archives, resolve their exact expected executables, and launch-smoke the Development build.
7. Scan project, test, cook, and package logs with zero project-originated errors or warnings.
8. In agent mode, capture the four acceptance views and complete the multimodal visual gate below. In human-local mode, report this gate as not applicable.
9. Manually walk the exact Shipping executable through both Rooms, both Dialogue Interactions, the complete Door cycle, restored input, and Escape exit at 2560 × 1440.
10. Create the versioned Shipping ZIP outside Git, record its SHA-256, and generate the local verification dashboard described by `verification-dashboard.md`.

Run focused gates while iterating, then run the complete command after all changes. A failed or skipped gate required by the active mode keeps verification red. A visual gate marked not applicable in human-local mode does not prevent the deterministic suite from passing.

From T04, the asset gate validates per-file provenance, hashes, complete art coverage, redistribution permission, and the 2K profile. The rendered scenario also captures Room A at 2560 × 1440. Agent mode requires a current six-criterion Room A review before it can pass; after inspecting the image and writing the linked review, complete that same run with `scripts/verify.ps1 -RequireVisualReview -CompleteVisualReview`. This completion mode rejects a changed working tree, different screenshot, missing criterion evidence, or another failed gate. See `docs/room-a.md` for the review schema. Human-local mode captures the image but marks agent judgement not applicable. This slice-specific gate does not replace T08's four-view final-art acceptance.

From T05, the same run also requires repeatable Room B and open-Door captures at 2560 × 1440 and separate current six-criterion agent reviews for both. Completion requires all three environment reviews; a Room A review alone is insufficient. Human-local mode captures all three and marks each agent judgement not applicable. The player-facing scenario additionally checks Room B circulation, guest-bed collision, and the inaccessible window boundary. See `docs/room-b.md` for camera positions and review instructions.

From T06, the same run also requires a 2560 × 1440 NPC A capture during the real Dialogue Interaction. Its current review includes the existing six criteria plus `npcPresentation` and `referenceBaseline`, each with visible evidence. All four reviews are required for completion. The player-facing scenario checks imported NPC A standing height in idle and dialogue, preserving the existing collision, replay, control restoration, and fresh-session checks. The UI pixel comparison uses a static floor patch beside the animated resident. The asset gate includes all character files, textures, animations, and imported content; the dashboard shows the pinned authoring-tool versions. See `docs/npc-a.md`. NPC B final art and T08's complete-prototype assessment remain separate.

### Incremental ticket profiles

From T07, also capture NPC B during its real Dialogue Interaction at 2560 x 1440
and require a current review with the six environment criteria plus
`npcPresentation` and `referenceBaseline`. All five slice reviews are required
for agent completion. The Player scenario checks both imported residents' idle
and dialogue scale, NPC B's visible gesture and facing direction, suspended and
restored input, and independent replay. Every NPC B source and imported asset
is covered by the same provenance, hash, redistribution, and 2K gates. See
`docs/npc-b.md`. Human-local mode captures all views without agent judgement;
T08's complete-prototype assessment remains separate.

From T08, the complete-prototype assessment is active. One final review covers
exactly four accepted views: Room A, NPC A during Dialogue Interaction, the open
Door, and Room B with NPC B. It requires the eight documented visual criteria
for every view plus cross-view coherence evidence. Each image is linked to the
tested revision, complete working-tree fingerprint, and SHA-256. Any reported
defect keeps the gate red. See `docs/visual-acceptance.md`.

From T09, canonical validation is a deliberately linked two-phase workflow. The
first run validates a separate clean checkout, produces both Win64 package
configurations, and records the exact Shipping executable. Run
`scripts/record-shipping-acceptance.ps1` to perform and record the complete
manual journey against that executable. Agents then use
`verify.ps1 -RequireVisualReview -CompleteVisualReview`; the visual completion
also completes delivery. Humans use `verify.ps1 -CompleteDelivery`. Completion
rejects a changed revision/fingerprint, changed executable hash, incomplete
manual checklist, any change to the complete accepted Shipping package, or a
deterministic failure, then creates the versioned ZIP and hash under
`C:\fpsOne-output\Delivery`.

From T10, the Player-facing scenario observes both live residents for at least
24 seconds. It requires planted feet, softly bent resting elbows, motion that
does not repeat at the former eight-second offset, distinct resident timing and
mannerisms, and two separated dialogue gesture beats per resident. Dismissal
and immediate replay are exercised at a raised-hand peak with a per-frame motion
bound. Current NPC A/NPC B captures and all existing visual reviews remain
required; temporal quality and close-angle penetration checks remain explicit
manual acceptance because a fixed screenshot cannot establish them.

Before a ticket introduces the feature exercised by a later gate, the verifier may mark that gate not applicable only when the result names the missing slice and the ticket that activates it. Through T03, repository tests cover the configured input surface, the player-facing world Interaction scenario is required, and the Development package must pass a launch smoke test. T03 requires both NPC exchanges, replay, collision, suspended scanning and walking, bounded mouse look, restored controls, and fresh-session reset alongside the existing Door checks. The four-view final-art agent visual gate activates with T08. These staged exceptions expire when their activating slices land and do not weaken the complete-prototype profile.

## Warning exceptions

Treat a diagnostic as an exception only when it originates outside project-controlled content, cannot be removed with the pinned toolchain, and has no effect on the verified workflows. Record its exact stable match, origin, evidence, and consequence in the verifier's exception manifest. Unrecorded warnings fail the run; broad filters are invalid.

## Multimodal visual gate

Once all four acceptance views exist, agent mode captures the Room A overview, NPC A at dialogue distance, open-door transition, and Room B with NPC B. A multimodal agent must inspect the resulting images at full available detail against the prototype's visual rubric, then write a pass/fail review tied to the tested Git revision and every screenshot hash. The review covers visible rendering failures, composition, lighting, material quality, furnishing density, NPC presentation, UI obstruction, and whether the images plausibly meet the documented unmodded Skyrim Special Edition/Fallout 4 PC Ultra benchmark at normal gameplay distance.

This gate is agent-mediated: the local script proves capture freshness and review linkage, while the multimodal inspection supplies the visual judgement. A missing, stale, or unevidenced review fails agent-mode verification. Human-local validation retains the deterministic Room A and UI captures but skips agent review without adding an external AI dependency.

## Performance

Record resolution and readily available frame timing with the acceptance capture. Performance is observational for this proof of concept and is not a hard gate. Do not add extended profiling unless observed performance prevents interaction or visual review.

## Completion evidence

Report both canonical commands and exit statuses, the dashboard path, both packaged-build paths, the Shipping acceptance record, the delivery ZIP and SHA-256, the inspected screenshots, the multimodal review result, and every exception. State any untested behaviour explicitly.
