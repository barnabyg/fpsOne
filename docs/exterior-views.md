# Exterior views: reproduction and acceptance

T11 gives both apartment windows lightweight, layered exterior scenery while
keeping the exterior inaccessible. Room A looks south over a warm parapet,
tree canopy, nearby roofs, and a restrained skyline. Room B looks east into a
planted residential courtyard. Both views share the same late-afternoon colour
temperature, architectural materials, scale, and horizon language, but their
silhouettes and depth cues are deliberately distinct.

## Editable source and layout

`scripts/room_a_assets.py` authors both the shared exterior materials and the
Room A assembly. `scripts/room_b_assets.py` authors the Room B assembly. The
six `M_Exterior*` materials, engine primitive geometry, and already-pinned
Poly Haven potted-plant mesh are the complete art inputs; there are no new
external assets or downloads. Rebuild them through the normal isolated,
transactional workflow:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\regenerate-assets.ps1
```

Room A retains the south parapet around `y=-420` cm, places warm roof masses and
tree forms from roughly `y=-590..-1180`, and uses cool skyline blocks around
`y=-2100..-2400`. Room B retains its east parapet and planters around
`x=600..675`, places the opposing facade around `x=1030`, and uses distant roof
masses around `x=1680..1840`. All new scenery has collision and cast shadows
disabled. The original window frames, sills, parapets, daylight, and collision
boundaries remain authoritative.

Generated actors carry `ExteriorScenery`, a Room-specific tag, and exactly one
of `ExteriorForeground`, `ExteriorMiddleDistance`, or `ExteriorDistant`. The
Player scenario rejects a missing layer or an actor whose bounds enter Room A
(`y > -270`) or Room B (`x < 440`). It also sweeps the real Player capsule into
both window assemblies and requires the same inaccessible stopping boundaries.

## Repeatable visual evidence

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -RequireVisualReview
```

The rendered scenario adds `roomAExterior` and `roomBExterior` to
`Saved/Verification/verification-result.json`. They are normal 2560 × 1440
gameplay views with the HUD and link their image, metadata, hash, and
`reviewPath`. Inspect each full-size image before writing its `review.json`:

```json
{
  "status": "passed",
  "reviewer": "Name of inspecting agent",
  "revision": "exact result.revision",
  "fingerprint": "exact result.fingerprint",
  "screenshotSha256": "exact view.sha256",
  "pairedScreenshotSha256": "exact counterpart exterior view.sha256",
  "criteria": {
    "depth": { "status": "passed", "evidence": "Foreground, middle, and distant cues visibly separate" },
    "scale": { "status": "passed", "evidence": "Windows, storeys, roofs, and planting read at residential scale" },
    "lightingContinuity": { "status": "passed", "evidence": "Exterior light and colour agree with the interior" },
    "seams": { "status": "passed", "evidence": "No gaps, leaks, clipping, or exposed backdrop edges are visible" },
    "renderingDefects": { "status": "passed", "evidence": "No missing material, broken geometry, or distracting artifact is visible" },
    "interiorComposition": { "status": "passed", "evidence": "The view supports rather than obscures the frame, sill, room, or navigation" },
    "propertyCoherence": { "status": "passed", "evidence": "Compared with the paired image: scale, horizon, sun, colour, and architecture read as one property" },
    "distinctness": { "status": "passed", "evidence": "Compared with the paired image: this outlook has a clearly different orientation and composition" }
  }
}
```

Each exterior review is hash-linked to both current exterior screenshots so
same-property coherence and distinctness cannot be assessed from one view in
isolation. Complete the unchanged run with
`scripts/verify.ps1 -RequireVisualReview -CompleteVisualReview`. Completion
requires these two reviews in addition to the five earlier slice reviews and
the separate T08 final four-view benchmark.

## Manual checks

At 2560 × 1440, launch the exact Shipping executable named by the verification
result. Walk laterally across Room A's south window, then inspect it closely.
Expect stable parallax between parapet, foliage/roofs, and skyline; warm
late-afternoon continuity; intact frame and sill; and no seams, light leaks,
clipping, or path outside. Repeat at Room B's east window. Expect a distinct
planted courtyard and opposing facade with the same property scale and lighting
language, stable parallax, intact trim, and no path outside. In both Rooms the
view must remain unobtrusive during normal navigation and Interaction.
