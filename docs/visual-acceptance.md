# T08 final visual acceptance

T08 assesses the furnished apartment and both residents as one finished testbed. The canonical agent run captures these four accepted 2560 × 1440 views through the real Player scenario:

1. Room A overview.
2. NPC A during its Dialogue Interaction.
3. The open-Door transition.
4. Room B with NPC B.

Run the first verification pass from the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -RequireVisualReview
```

All deterministic gates and captures must pass. The Visual acceptance gate remains red until `Saved\Verification\final-visual-review.json` contains one assessment of the four current images. The review uses this shape:

```json
{
  "status": "passed",
  "reviewer": "Multimodal agent",
  "revision": "<verification-result revision>",
  "fingerprint": "<verification-result fingerprint>",
  "coherence": { "status": "passed", "evidence": "Visible evidence across all four views." },
  "views": {
    "roomA": {
      "screenshotSha256": "<verification-result roomA sha256>",
      "criteria": {
        "composition": { "status": "passed", "evidence": "Visible evidence." },
        "lighting": { "status": "passed", "evidence": "Visible evidence including shadows and reflections." },
        "materials": { "status": "passed", "evidence": "Visible evidence." },
        "density": { "status": "passed", "evidence": "Visible evidence." },
        "renderingDefects": { "status": "passed", "evidence": "Visible evidence." },
        "npcPresentation": { "status": "passed", "evidence": "Visible evidence, or why the NPC presentation visible in this view passes." },
        "uiObstruction": { "status": "passed", "evidence": "Visible evidence." },
        "referenceBaseline": { "status": "passed", "evidence": "Comparison with unmodded Skyrim Special Edition/Fallout 4 PC Ultra at normal gameplay distance." }
      }
    }
  }
}
```

Repeat that complete criterion object for `npcA`, `doorTransition`, and `roomB`; extra or missing views are rejected. A visible material defect must set the affected criterion and top-level status to `failed`. The gate stays red until the defect is fixed, fresh images are captured, and all criteria pass.

The T04–T07 slice reviews remain required because they retain their narrower evidence history. After writing those five `review.json` files and the final review, complete the unchanged run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -RequireVisualReview -CompleteVisualReview
```

Completion re-hashes every image, checks the tested revision and complete working-tree fingerprint, verifies every criterion, and updates the dashboard without recapturing. The dashboard records full-size image links, hashes, observational frame times, logs, reports, and the packaged build.
